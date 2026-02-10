"""Nourish API — Mahlzeiten erfassen und verwalten."""

import logging
import json as json_mod
from datetime import date as date_type, datetime, time as time_type
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.schemas import (
    VoiceInput, TextInput, PhotoInput, MealUpdate, MealResponse, MealType, NutrientProfile,
)
from app.services.claude_service import parse_food_input, generate_meal_feedback
from app.services.nutrition_service import lookup_food, calculate_nutrients

log = logging.getLogger(__name__)
router = APIRouter()


# ── Einheiten-Umrechnung: Stück/EL/TL/etc. → Gramm ──

# Durchschnittsgewichte pro Stück (in Gramm)
_WEIGHT_PER_PIECE: dict[str, float] = {
    "ei": 60.0, "eier": 60.0, "hühnerei": 60.0,
    "avocado": 150.0,
    "apfel": 180.0, "banane": 120.0, "orange": 170.0,
    "tomate": 120.0, "tomaten": 120.0, "cherrytomate": 15.0, "cherrytomaten": 15.0,
    "kartoffel": 150.0, "kartoffeln": 150.0,
    "zwiebel": 80.0, "knoblauchzehe": 4.0, "knoblauch": 4.0,
    "paprika": 160.0,
    "gurke": 400.0, "salatgurke": 400.0,
    "möhre": 80.0, "karotte": 80.0, "möhren": 80.0, "karotten": 80.0,
    "brötchen": 60.0, "scheibe brot": 50.0,
    "kiwi": 75.0, "pfirsich": 150.0, "birne": 180.0, "pflaume": 60.0,
    "mandarine": 70.0, "zitrone": 80.0,
}

# Generische Einheiten-Gewichte (in Gramm)
_UNIT_GRAMS: dict[str, float] = {
    "g": 1.0,
    "kg": 1000.0,
    "ml": 1.0,
    "l": 1000.0,
    "el": 15.0,        # Esslöffel
    "tl": 5.0,         # Teelöffel
    "esslöffel": 15.0,
    "teelöffel": 5.0,
    "tasse": 250.0,
    "becher": 200.0,
    "glas": 250.0,
    "handvoll": 40.0,
    "scheibe": 30.0,    # Brot, Käse, Wurst
    "portion": 200.0,
    "packung": 200.0,
    "dose": 400.0,
}


def _normalize_grams(name: str, amount: float, unit: str) -> float:
    """Rechnet Menge + Einheit in Gramm um.

    Logik:
    1. Einheit ist g/kg/ml/l → direkte Umrechnung
    2. Einheit ist 'Stück' → Lookup im Stückgewicht-Dict
    3. Einheit ist EL/TL/Tasse/etc. → generisches Gewicht
    4. Fallback: amount als Gramm (wenn Einheit unbekannt)
    """
    unit_lower = unit.lower().strip()
    name_lower = name.lower().strip()

    # 1. Direkte metrische Einheiten
    if unit_lower in ("g", "kg", "ml", "l"):
        factor = _UNIT_GRAMS.get(unit_lower, 1.0)
        grams = amount * factor
        log.info("[UNIT] %s: %.1f %s → %.0fg (metrisch)", name, amount, unit, grams)
        return grams

    # 2. Stück → lebensmittelspezifisches Gewicht
    if unit_lower in ("stück", "stk", "stk.", "st"):
        piece_weight = _WEIGHT_PER_PIECE.get(name_lower, 100.0)
        grams = amount * piece_weight
        log.info("[UNIT] %s: %.0f Stück × %.0fg = %.0fg", name, amount, piece_weight, grams)
        return grams

    # 3. Generische Einheiten (EL, TL, Tasse, Scheibe, etc.)
    generic = _UNIT_GRAMS.get(unit_lower)
    if generic:
        grams = amount * generic
        log.info("[UNIT] %s: %.1f %s × %.0fg = %.0fg", name, amount, unit, generic, grams)
        return grams

    # 4. Fallback: Einheit unbekannt, nehme amount als Gramm
    log.warning("[UNIT] Unbekannte Einheit '%s' fuer '%s', nehme %.0f als Gramm", unit, name, amount)
    return amount


async def _process_meal(
    parsed_items: list[dict],
    meal_type: MealType,
    input_method: str,
    raw_input: str,
    user: dict,
    db: AsyncSession,
    meal_time: time_type | None = None,
) -> MealResponse:
    """Gemeinsame Logik für alle Eingabemethoden."""
    effective_time = meal_time or datetime.now().time().replace(second=0, microsecond=0)

    # 1. Mahlzeit-Eintrag erstellen
    result = await db.execute(
        text("""
            INSERT INTO food_entries (user_id, meal_type, input_method, raw_input, meal_date, meal_time)
            VALUES (:uid, :mt, :im, :raw, :date, :mtime)
            RETURNING id, logged_at
        """),
        {
            "uid": user["id"], "mt": meal_type.value,
            "im": input_method, "raw": raw_input,
            "date": date_type.today(), "mtime": effective_time,
        },
    )
    entry = result.mappings().first()
    entry_id = entry["id"]

    # 2. Für jedes Item: Nährstoffe nachschlagen und berechnen
    food_items = []
    for i, item in enumerate(parsed_items):
        # Nährstoffe finden (erst persönliche Bibliothek, dann extern)
        # TODO: Erst in products des Users suchen
        food_data = await lookup_food(item["name"], db=db)

        nutrients = None
        normalized_grams = _normalize_grams(
            item["name"], item["amount"], item.get("unit", "g")
        )

        if food_data and "nutrients_per_100" in food_data:
            nutrients = calculate_nutrients(
                food_data["nutrients_per_100"], normalized_grams,
                food_name=f"{item['name']} (→ {food_data.get('name', '?')} via {food_data.get('source', '?')})",
            )

        await db.execute(
            text("""
                INSERT INTO food_items (food_entry_id, name, amount, unit, normalized_grams, calculated_nutrients, sort_order)
                VALUES (:eid, :name, :amount, :unit, :grams, :nutrients, :order)
            """),
            {
                "eid": entry_id, "name": item["name"],
                "amount": item["amount"], "unit": item.get("unit", "g"),
                "grams": normalized_grams,
                "nutrients": nutrients.model_dump_json() if nutrients else None,
                "order": i,
            },
        )

        food_items.append({
            "id": str(entry_id),  # Vereinfachung
            "name": item["name"],
            "amount": item["amount"],
            "unit": item.get("unit", "g"),
            "normalized_grams": normalized_grams,
            "calculated_nutrients": nutrients,
        })

    # 3. KI-Feedback generieren
    # TODO: Tagesbilanz aus daily_logs holen
    daily_balance = {}  # Placeholder
    ai_feedback = await generate_meal_feedback(parsed_items, user, daily_balance)

    # 4. Feedback speichern
    await db.execute(
        text("UPDATE food_entries SET ai_feedback = :fb WHERE id = :eid"),
        {"fb": ai_feedback, "eid": entry_id},
    )
    await db.commit()

    # Gesamtkalorien/-protein berechnen
    total_cal = sum(
        fi["calculated_nutrients"].calories
        for fi in food_items
        if fi["calculated_nutrients"]
    )
    total_prot = sum(
        fi["calculated_nutrients"].protein
        for fi in food_items
        if fi["calculated_nutrients"]
    )

    return MealResponse(
        id=str(entry_id),
        meal_type=meal_type,
        input_method=input_method,
        items=food_items,
        ai_feedback=ai_feedback,
        ai_feedback_knowledge_links=[],
        logged_at=entry["logged_at"],
        meal_time=effective_time.strftime("%H:%M"),
        total_calories=total_cal,
        total_protein=total_prot,
    )


def _parse_meal_time(meal_time_str: str | None) -> time_type:
    """Parst 'HH:MM' String zu time. Fallback: aktuelle Serverzeit."""
    if meal_time_str:
        try:
            parts = meal_time_str.strip().split(":")
            return time_type(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            log.warning("[TIME] Konnte '%s' nicht parsen, nutze aktuelle Zeit", meal_time_str)
    return datetime.now().time().replace(second=0, microsecond=0)


def _detect_meal_type_from_text(raw_input: str) -> MealType | None:
    """Erkennt den Mahlzeittyp aus Keywords im Text. Gibt None zurueck wenn nichts erkannt."""
    lower = raw_input.lower()
    breakfast_kw = ("frühstück", "morgens", "morning", "zum frühstück", "heute morgen")
    lunch_kw = ("mittag", "mittagessen", "lunch", "zum mittag")
    dinner_kw = ("abend", "abendessen", "abendbrot", "dinner", "zum abend")
    snack_kw = ("snack", "zwischendurch", "zwischenmahlzeit", "nachmittags")

    for kw in breakfast_kw:
        if kw in lower:
            return MealType.breakfast
    for kw in lunch_kw:
        if kw in lower:
            return MealType.lunch
    for kw in dinner_kw:
        if kw in lower:
            return MealType.dinner
    for kw in snack_kw:
        if kw in lower:
            return MealType.snack
    return None


def _detect_meal_type_from_time(meal_time: time_type) -> MealType:
    """Leitet den Mahlzeittyp aus der Uhrzeit ab."""
    h, m = meal_time.hour, meal_time.minute
    minutes = h * 60 + m
    if 300 <= minutes < 600:       # 05:00-10:00
        return MealType.breakfast
    elif 600 <= minutes < 690:     # 10:00-11:30
        return MealType.snack
    elif 690 <= minutes < 870:     # 11:30-14:30
        return MealType.lunch
    elif 870 <= minutes < 1020:    # 14:30-17:00
        return MealType.snack
    elif 1020 <= minutes < 1260:   # 17:00-21:00
        return MealType.dinner
    else:                          # 21:00-05:00
        return MealType.snack


@router.post("/voice", response_model=MealResponse)
async def create_meal_voice(
    body: VoiceInput,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verarbeitet Spracheingabe → Mahlzeit."""
    parsed = await parse_food_input(body.transcript)
    parsed_items = parsed["items"]
    if not parsed_items:
        raise HTTPException(400, "Konnte keine Lebensmittel erkennen. Bitte nochmal versuchen.")

    meal_time = _parse_meal_time(parsed.get("meal_time"))
    meal_type = body.meal_type or _detect_meal_type_from_text(body.transcript) or _detect_meal_type_from_time(meal_time)
    return await _process_meal(parsed_items, meal_type, "voice", body.transcript, user, db, meal_time=meal_time)


@router.post("/text", response_model=MealResponse)
async def create_meal_text(
    body: TextInput,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verarbeitet Texteingabe → Mahlzeit."""
    parsed = await parse_food_input(body.text)
    parsed_items = parsed["items"]
    if not parsed_items:
        raise HTTPException(400, "Konnte keine Lebensmittel erkennen.")

    meal_time = _parse_meal_time(parsed.get("meal_time"))
    meal_type = body.meal_type or _detect_meal_type_from_text(body.text) or _detect_meal_type_from_time(meal_time)
    return await _process_meal(parsed_items, meal_type, "text", body.text, user, db, meal_time=meal_time)


@router.get("", response_model=list[MealResponse])
async def get_meals(
    meal_date: date_type = Query(default=None, alias="date"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alle Mahlzeiten für ein Datum (Standard: heute)."""
    target_date = meal_date or date_type.today()

    result = await db.execute(
        text("""
            SELECT fe.id, fe.meal_type, fe.input_method, fe.ai_feedback,
                   fe.ai_feedback_knowledge_links, fe.logged_at,
                   fe.meal_time,
                   COALESCE(json_agg(json_build_object(
                       'id', fi.id, 'name', fi.name, 'amount', fi.amount,
                       'unit', fi.unit, 'normalized_grams', fi.normalized_grams,
                       'calculated_nutrients', fi.calculated_nutrients
                   ) ORDER BY fi.sort_order) FILTER (WHERE fi.id IS NOT NULL), '[]') as items
            FROM food_entries fe
            LEFT JOIN food_items fi ON fi.food_entry_id = fe.id
            WHERE fe.user_id = :uid AND fe.meal_date = :date
            GROUP BY fe.id
            ORDER BY fe.meal_time ASC NULLS LAST, fe.logged_at ASC
        """),
        {"uid": user["id"], "date": target_date},
    )

    meals = []
    for row in result.mappings():
        items_data = row["items"]
        if isinstance(items_data, str):
            items_data = json_mod.loads(items_data)

        total_cal = 0.0
        total_prot = 0.0
        parsed_items = []
        for item in items_data:
            nutrients = item.get("calculated_nutrients")
            if isinstance(nutrients, str):
                nutrients = json_mod.loads(nutrients)
            if nutrients:
                total_cal += nutrients.get("calories", 0) or 0
                total_prot += nutrients.get("protein", 0) or 0
            parsed_items.append({
                "id": item["id"],
                "name": item["name"],
                "amount": item["amount"],
                "unit": item["unit"],
                "normalized_grams": item.get("normalized_grams"),
                "calculated_nutrients": NutrientProfile(**nutrients) if nutrients else None,
            })

        mt = row["meal_time"]
        meal_time_str = mt.strftime("%H:%M") if mt else None

        meals.append(MealResponse(
            id=row["id"],
            meal_type=row["meal_type"],
            input_method=row["input_method"],
            items=parsed_items,
            ai_feedback=row["ai_feedback"],
            ai_feedback_knowledge_links=row["ai_feedback_knowledge_links"] or [],
            logged_at=row["logged_at"],
            meal_time=meal_time_str,
            total_calories=round(total_cal, 1),
            total_protein=round(total_prot, 1),
        ))

    return meals


@router.put("/{meal_id}", response_model=MealResponse)
async def update_meal(
    meal_id: str,
    body: MealUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bearbeitet eine Mahlzeit: meal_type, meal_time und/oder Items aendern."""

    # 1. Bestehenden Eintrag laden + Ownership pruefen
    result = await db.execute(
        text("""
            SELECT id, meal_type, input_method, raw_input, ai_feedback,
                   ai_feedback_knowledge_links, logged_at, meal_time
            FROM food_entries
            WHERE id = :mid AND user_id = :uid
        """),
        {"mid": meal_id, "uid": user["id"]},
    )
    entry = result.mappings().first()
    if not entry:
        raise HTTPException(404, "Mahlzeit nicht gefunden")

    # 2. Felder bestimmen (neu oder bestehendes beibehalten)
    new_meal_type = body.meal_type.value if body.meal_type else entry["meal_type"]
    new_meal_time = entry["meal_time"]
    if body.meal_time is not None:
        new_meal_time = _parse_meal_time(body.meal_time)

    # 3. Falls neuer Text: Items komplett neu parsen
    if body.text:
        parsed = await parse_food_input(body.text)
        parsed_items = parsed["items"]
        if not parsed_items:
            raise HTTPException(400, "Konnte keine Lebensmittel im neuen Text erkennen.")

        # Alte Items loeschen
        await db.execute(
            text("DELETE FROM food_items WHERE food_entry_id = :eid"),
            {"eid": entry["id"]},
        )

        # Neue Items anlegen
        food_items = []
        for i, item in enumerate(parsed_items):
            food_data = await lookup_food(item["name"], db=db)
            nutrients = None
            normalized_grams = _normalize_grams(
                item["name"], item["amount"], item.get("unit", "g")
            )
            if food_data and "nutrients_per_100" in food_data:
                nutrients = calculate_nutrients(
                    food_data["nutrients_per_100"], normalized_grams,
                    food_name=f"{item['name']} (→ {food_data.get('name', '?')} via {food_data.get('source', '?')})",
                )
            await db.execute(
                text("""
                    INSERT INTO food_items (food_entry_id, name, amount, unit, normalized_grams, calculated_nutrients, sort_order)
                    VALUES (:eid, :name, :amount, :unit, :grams, :nutrients, :order)
                """),
                {
                    "eid": entry["id"], "name": item["name"],
                    "amount": item["amount"], "unit": item.get("unit", "g"),
                    "grams": normalized_grams,
                    "nutrients": nutrients.model_dump_json() if nutrients else None,
                    "order": i,
                },
            )
            food_items.append({
                "id": str(entry["id"]),
                "name": item["name"],
                "amount": item["amount"],
                "unit": item.get("unit", "g"),
                "normalized_grams": normalized_grams,
                "calculated_nutrients": nutrients,
            })

        # Neues AI-Feedback generieren
        daily_balance = {}
        ai_feedback = await generate_meal_feedback(parsed_items, user, daily_balance)

        # Entry updaten (inkl. raw_input und ai_feedback)
        await db.execute(
            text("""
                UPDATE food_entries
                SET meal_type = :mt, meal_time = :mtime, raw_input = :raw, ai_feedback = :fb
                WHERE id = :eid
            """),
            {
                "mt": new_meal_type, "mtime": new_meal_time,
                "raw": body.text, "fb": ai_feedback, "eid": entry["id"],
            },
        )
    else:
        # Nur meal_type/meal_time updaten, Items beibehalten
        await db.execute(
            text("UPDATE food_entries SET meal_type = :mt, meal_time = :mtime WHERE id = :eid"),
            {"mt": new_meal_type, "mtime": new_meal_time, "eid": entry["id"]},
        )
        ai_feedback = entry["ai_feedback"]

        # Bestehende Items laden
        items_result = await db.execute(
            text("""
                SELECT id, name, amount, unit, normalized_grams, calculated_nutrients
                FROM food_items WHERE food_entry_id = :eid ORDER BY sort_order
            """),
            {"eid": entry["id"]},
        )
        food_items = []
        for fi in items_result.mappings():
            nutrients = fi["calculated_nutrients"]
            if isinstance(nutrients, str):
                nutrients = json_mod.loads(nutrients)
            food_items.append({
                "id": fi["id"],
                "name": fi["name"],
                "amount": fi["amount"],
                "unit": fi["unit"],
                "normalized_grams": fi["normalized_grams"],
                "calculated_nutrients": NutrientProfile(**nutrients) if nutrients else None,
            })

    await db.commit()

    # Totals berechnen
    total_cal = sum(
        (fi["calculated_nutrients"].calories if hasattr(fi["calculated_nutrients"], "calories") else fi["calculated_nutrients"].get("calories", 0))
        for fi in food_items if fi["calculated_nutrients"]
    )
    total_prot = sum(
        (fi["calculated_nutrients"].protein if hasattr(fi["calculated_nutrients"], "protein") else fi["calculated_nutrients"].get("protein", 0))
        for fi in food_items if fi["calculated_nutrients"]
    )

    mt_str = new_meal_time.strftime("%H:%M") if hasattr(new_meal_time, "strftime") else str(new_meal_time)[:5] if new_meal_time else None

    return MealResponse(
        id=entry["id"],
        meal_type=new_meal_type,
        input_method=entry["input_method"],
        items=food_items,
        ai_feedback=ai_feedback,
        ai_feedback_knowledge_links=entry["ai_feedback_knowledge_links"] or [],
        logged_at=entry["logged_at"],
        meal_time=mt_str,
        total_calories=round(total_cal, 1),
        total_protein=round(total_prot, 1),
    )


@router.delete("/{meal_id}")
async def delete_meal(
    meal_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Löscht eine Mahlzeit."""
    result = await db.execute(
        text("DELETE FROM food_entries WHERE id = :mid AND user_id = :uid RETURNING id"),
        {"mid": meal_id, "uid": user["id"]},
    )
    if not result.first():
        raise HTTPException(404, "Mahlzeit nicht gefunden")
    await db.commit()
    return {"deleted": True}
