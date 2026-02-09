"""Nourish Backend — Nährstoff-Aggregation, Zielwert-Berechnung und Defizit-Analyse."""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.schemas import NutrientProfile


# ── Alle summierbaren Felder im NutrientProfile ──
_NUTRIENT_FIELDS = [f.strip() for f in """
    calories protein carbs carbs_sugar carbs_sugar_glucose carbs_sugar_fructose
    carbs_starch fiber fat fat_saturated fat_mono fat_poly fat_omega3 fat_omega6
    fat_trans sodium vitamin_a vitamin_b1 vitamin_b2 vitamin_b3 vitamin_b5
    vitamin_b6 vitamin_b7 vitamin_b9 vitamin_b12 vitamin_c vitamin_d vitamin_e
    vitamin_k calcium magnesium potassium phosphorus iron zinc copper iodine
    selenium manganese chromium molybdenum caffeine alcohol
""".split()]


# ── Aktivitätsfaktoren (Harris-Benedict) ──
_ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# ── Makro-Splits je Gesundheitsziel (Protein/Carbs/Fat in % der Kalorien) ──
_MACRO_SPLITS = {
    "muscle_gain":    (0.30, 0.40, 0.30),
    "fat_loss":       (0.35, 0.30, 0.35),
    "maintenance":    (0.25, 0.45, 0.30),
    "energy":         (0.20, 0.50, 0.30),
    "longevity":      (0.25, 0.40, 0.35),
    "general_health": (0.25, 0.45, 0.30),
}


async def aggregate_daily_nutrients(
    user_id: str,
    target_date: date,
    db: AsyncSession,
) -> NutrientProfile:
    """
    Summiert alle calculated_nutrients aus food_items fuer food_entries
    des Users an einem bestimmten Datum.
    """
    result = await db.execute(
        text("""
            SELECT fi.calculated_nutrients
            FROM food_items fi
            JOIN food_entries fe ON fe.id = fi.food_entry_id
            WHERE fe.user_id = :uid AND fe.meal_date = :date
              AND fi.calculated_nutrients IS NOT NULL
        """),
        {"uid": user_id, "date": target_date},
    )

    rows = result.mappings().all()

    # Alle Naehrstoffwerte aufsummieren
    totals: dict[str, float] = {field: 0.0 for field in _NUTRIENT_FIELDS}

    for row in rows:
        nutrients = row["calculated_nutrients"]
        # JSONB wird je nach Treiber als dict oder als str zurueckgegeben
        if isinstance(nutrients, str):
            import json
            nutrients = json.loads(nutrients)
        if not isinstance(nutrients, dict):
            continue
        for field in _NUTRIENT_FIELDS:
            value = nutrients.get(field, 0)
            if isinstance(value, (int, float)):
                totals[field] += value

    # Auf 2 Nachkommastellen runden
    rounded = {k: round(v, 2) for k, v in totals.items()}
    return NutrientProfile(**rounded)


def calculate_target_nutrients(user: dict) -> NutrientProfile:
    """
    Berechnet Soll-Naehrstoffe basierend auf Nutzerprofil.
    Grundumsatz via Harris-Benedict, Mikros nach DGE-Empfehlungen.
    """
    gender = user.get("gender", "diverse")
    weight = float(user.get("weight_kg") or 70.0)
    height = float(user.get("height_cm") or 170)
    activity = user.get("activity_level", "moderate")
    goal = user.get("health_goal", "general_health")

    # Alter aus birth_date berechnen
    birth_date = user.get("birth_date")
    if birth_date:
        if isinstance(birth_date, str):
            birth_date = date.fromisoformat(birth_date)
        today = date.today()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
    else:
        age = 30  # Fallback

    # ── Grundumsatz (Harris-Benedict) ──
    if gender == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    elif gender == "female":
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    else:
        # Mittelwert fuer diverse / prefer_not_to_say
        bmr_m = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        bmr_f = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        bmr = (bmr_m + bmr_f) / 2

    # Gesamtumsatz (TDEE)
    factor = _ACTIVITY_FACTORS.get(activity, 1.55)
    tdee = bmr * factor

    # Ziel-Anpassung
    if goal == "fat_loss":
        target_calories = tdee - 500  # Moderates Defizit
    elif goal == "muscle_gain":
        target_calories = tdee + 300  # Leichter Ueberschuss
    else:
        target_calories = tdee

    target_calories = max(target_calories, 1200)  # Minimum Sicherheitsgrenze

    # ── Makros ──
    prot_pct, carb_pct, fat_pct = _MACRO_SPLITS.get(goal, (0.25, 0.45, 0.30))
    protein = (target_calories * prot_pct) / 4     # 4 kcal/g
    carbs = (target_calories * carb_pct) / 4        # 4 kcal/g
    fat = (target_calories * fat_pct) / 9            # 9 kcal/g
    fiber = 30.0  # DGE-Empfehlung: mind. 30g/Tag

    # ── Mikros (DGE-Empfehlungen, vereinfacht nach Geschlecht/Alter) ──
    is_female = gender == "female"

    targets = NutrientProfile(
        calories=round(target_calories),
        protein=round(protein, 1),
        carbs=round(carbs, 1),
        carbs_sugar=50.0,           # WHO: max. 10% der Kalorien ≈ 50g bei 2000 kcal
        carbs_sugar_glucose=0,
        carbs_sugar_fructose=0,
        carbs_starch=0,
        fiber=fiber,
        fat=round(fat, 1),
        fat_saturated=round(target_calories * 0.10 / 9, 1),  # Max 10% der Kalorien
        fat_mono=round(target_calories * 0.13 / 9, 1),
        fat_poly=round(target_calories * 0.07 / 9, 1),
        fat_omega3=_dge_omega3(is_female),
        fat_omega6=_dge_omega6(is_female),
        fat_trans=0,
        sodium=1500.0,             # DGE: 1500mg/Tag

        # Vitamine
        vitamin_a=800.0 if is_female else 1000.0,        # µg Retinol-Äquivalent
        vitamin_b1=1.0 if is_female else 1.2,             # mg
        vitamin_b2=1.1 if is_female else 1.4,             # mg
        vitamin_b3=13.0 if is_female else 16.0,           # mg NE
        vitamin_b5=6.0,                                    # mg
        vitamin_b6=1.4 if age > 65 else 1.2 if is_female else 1.5 if age <= 65 else 1.6,
        vitamin_b7=40.0,                                   # µg Biotin
        vitamin_b9=300.0,                                  # µg Folat-Äquivalent
        vitamin_b12=4.0,                                   # µg
        vitamin_c=95.0 if is_female else 110.0,           # mg
        vitamin_d=20.0,                                    # µg (bei unzureichender Sonnenexposition)
        vitamin_e=12.0 if is_female else 14.0,            # mg Alpha-Tocopherol
        vitamin_k=60.0 if is_female else 70.0,            # µg

        # Mineralstoffe
        calcium=1000.0,                                    # mg
        magnesium=300.0 if is_female else 350.0,          # mg
        potassium=4000.0,                                  # mg
        phosphorus=700.0,                                  # mg
        iron=15.0 if (is_female and age < 51) else 10.0,  # mg (Frauen prä-menopausal höher)
        zinc=7.0 if is_female else 10.0,                  # mg
        copper=1.0,                                        # mg
        iodine=200.0,                                      # µg
        selenium=60.0 if is_female else 70.0,             # µg
        manganese=3.0,                                     # mg
        chromium=30.0 if is_female else 35.0,             # µg
        molybdenum=50.0,                                   # µg

        caffeine=400.0,                                    # mg max. (EFSA)
        alcohol=0,                                         # Ziel: 0
    )

    return targets


def _dge_omega3(is_female: bool) -> float:
    """DGE-Empfehlung Omega-3: 0.5% der Gesamtenergie ≈ 1.1-1.6g/Tag."""
    return 1.1 if is_female else 1.6


def _dge_omega6(is_female: bool) -> float:
    """DGE-Empfehlung Omega-6: 2.5% der Gesamtenergie ≈ 5-7g/Tag."""
    return 5.0 if is_female else 7.0


def calculate_deficits(
    actual: NutrientProfile,
    target: NutrientProfile,
) -> dict:
    """
    Vergleicht Ist- mit Soll-Naehrstoffen.
    Gibt fuer jeden Naehrstoff actual, target, percentage und Status zurueck.
    Status: "deficit" (<80%), "ok" (80-120%), "excess" (>120%).
    """
    result = {}

    for field in _NUTRIENT_FIELDS:
        actual_val = getattr(actual, field, 0) or 0
        target_val = getattr(target, field, 0) or 0

        if target_val > 0:
            percentage = round((actual_val / target_val) * 100, 1)
        else:
            # Kein Zielwert definiert (z.B. Alkohol = 0)
            percentage = 0 if actual_val == 0 else 100

        if percentage < 80:
            status = "deficit"
        elif percentage > 120:
            status = "excess"
        else:
            status = "ok"

        result[field] = {
            "actual": round(actual_val, 2),
            "target": round(target_val, 2),
            "percentage": percentage,
            "status": status,
        }

    return result


async def get_week_trends(
    user_id: str,
    db: AsyncSession,
) -> dict:
    """
    Berechnet 7-Tage-Durchschnitt aller Naehrstoffe und identifiziert
    chronische Defizite/Ueberschuesse (>= 5 von 7 Tagen).
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=6)

    result = await db.execute(
        text("""
            SELECT log_date, actual_nutrients, target_nutrients
            FROM daily_logs
            WHERE user_id = :uid AND log_date BETWEEN :start AND :end
            ORDER BY log_date
        """),
        {"uid": user_id, "start": start_date, "end": end_date},
    )
    logs = result.mappings().all()

    if not logs:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "days_tracked": 0,
            "averages": {},
            "chronic_deficits": [],
            "chronic_excesses": [],
        }

    # Naehrstoff-Summen und Deficit-Zaehler pro Tag sammeln
    sums: dict[str, float] = {f: 0.0 for f in _NUTRIENT_FIELDS}
    deficit_counts: dict[str, int] = {f: 0 for f in _NUTRIENT_FIELDS}
    excess_counts: dict[str, int] = {f: 0 for f in _NUTRIENT_FIELDS}
    days_tracked = len(logs)

    for log in logs:
        actual_raw = log["actual_nutrients"]
        target_raw = log["target_nutrients"]

        if isinstance(actual_raw, str):
            import json
            actual_raw = json.loads(actual_raw)
        if isinstance(target_raw, str):
            import json
            target_raw = json.loads(target_raw)

        if not actual_raw:
            continue

        for field in _NUTRIENT_FIELDS:
            val = actual_raw.get(field, 0) or 0
            sums[field] += val

            target_val = (target_raw or {}).get(field, 0) or 0
            if target_val > 0:
                pct = (val / target_val) * 100
                if pct < 80:
                    deficit_counts[field] += 1
                elif pct > 120:
                    excess_counts[field] += 1

    # Durchschnittswerte berechnen
    averages = {f: round(sums[f] / days_tracked, 2) for f in _NUTRIENT_FIELDS}

    # Chronische Defizite: >= 5 von den getrackteten Tagen
    threshold = min(5, days_tracked)  # Bei weniger als 5 Tagen: alle muessen betroffen sein
    chronic_deficits = [
        {"nutrient": f, "deficit_days": deficit_counts[f], "avg_value": averages[f]}
        for f in _NUTRIENT_FIELDS
        if deficit_counts[f] >= threshold and f not in ("caffeine", "alcohol", "fat_trans")
    ]
    chronic_excesses = [
        {"nutrient": f, "excess_days": excess_counts[f], "avg_value": averages[f]}
        for f in _NUTRIENT_FIELDS
        if excess_counts[f] >= threshold and f not in ("caffeine", "alcohol")
    ]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "days_tracked": days_tracked,
        "averages": averages,
        "chronic_deficits": chronic_deficits,
        "chronic_excesses": chronic_excesses,
    }
