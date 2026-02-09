"""Nourish API — Tagesbilanz."""

import json
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.schemas import DailyLogResponse, NutrientProfile
from app.services.balance_service import (
    aggregate_daily_nutrients,
    calculate_target_nutrients,
    calculate_deficits,
    get_week_trends,
)

router = APIRouter()


@router.get("/", response_model=DailyLogResponse)
async def get_daily_log(
    log_date: date = Query(default=None, alias="date"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tagesbilanz für ein Datum (Standard: heute)."""
    target_date = log_date or date.today()
    user_id = user["id"]

    # Ist-Naehrstoffe aus food_items aggregieren
    actual = await aggregate_daily_nutrients(user_id, target_date, db)

    # Soll-Naehrstoffe: aus User-Profil oder frisch berechnen
    user_target = user.get("target_nutrients")
    if user_target:
        if isinstance(user_target, str):
            user_target = json.loads(user_target)
        target = NutrientProfile(**user_target)
    else:
        target = calculate_target_nutrients(user)

    # Defizite berechnen
    deficits = calculate_deficits(actual, target)

    # UPSERT in daily_logs — Tagesbilanz speichern/aktualisieren
    await db.execute(
        text("""
            INSERT INTO daily_logs (user_id, log_date, target_nutrients, actual_nutrients,
                                    caffeine_total_mg, alcohol_total_g)
            VALUES (:uid, :date, :target, :actual, :caffeine, :alcohol)
            ON CONFLICT (user_id, log_date)
            DO UPDATE SET
                target_nutrients = EXCLUDED.target_nutrients,
                actual_nutrients = EXCLUDED.actual_nutrients,
                caffeine_total_mg = EXCLUDED.caffeine_total_mg,
                alcohol_total_g = EXCLUDED.alcohol_total_g,
                updated_at = NOW()
        """),
        {
            "uid": user_id,
            "date": target_date,
            "target": target.model_dump_json(),
            "actual": actual.model_dump_json(),
            "caffeine": actual.caffeine,
            "alcohol": actual.alcohol,
        },
    )

    # Mahlzeiten des Tages laden
    meals_result = await db.execute(
        text("""
            SELECT fe.id, fe.meal_type, fe.input_method, fe.ai_feedback,
                   fe.ai_feedback_knowledge_links, fe.logged_at,
                   COALESCE(json_agg(json_build_object(
                       'id', fi.id, 'name', fi.name, 'amount', fi.amount,
                       'unit', fi.unit, 'normalized_grams', fi.normalized_grams,
                       'calculated_nutrients', fi.calculated_nutrients
                   ) ORDER BY fi.sort_order) FILTER (WHERE fi.id IS NOT NULL), '[]') as items
            FROM food_entries fe
            LEFT JOIN food_items fi ON fi.food_entry_id = fe.id
            WHERE fe.user_id = :uid AND fe.meal_date = :date
            GROUP BY fe.id
            ORDER BY fe.logged_at
        """),
        {"uid": user_id, "date": target_date},
    )
    meals_rows = meals_result.mappings().all()

    # Mahlzeiten fuer Response aufbereiten
    meals = []
    for row in meals_rows:
        items_data = row["items"]
        if isinstance(items_data, str):
            items_data = json.loads(items_data)

        total_cal = 0.0
        total_prot = 0.0
        parsed_items = []
        for item in items_data:
            nutrients = item.get("calculated_nutrients")
            if isinstance(nutrients, str):
                nutrients = json.loads(nutrients)
            if nutrients:
                total_cal += nutrients.get("calories", 0) or 0
                total_prot += nutrients.get("protein", 0) or 0
            parsed_items.append({
                "id": str(item["id"]),
                "name": item["name"],
                "amount": item["amount"],
                "unit": item["unit"],
                "normalized_grams": item.get("normalized_grams"),
                "calculated_nutrients": NutrientProfile(**nutrients) if nutrients else None,
            })

        meals.append({
            "id": str(row["id"]),
            "meal_type": row["meal_type"],
            "input_method": row["input_method"],
            "items": parsed_items,
            "ai_feedback": row["ai_feedback"],
            "ai_feedback_knowledge_links": row["ai_feedback_knowledge_links"] or [],
            "logged_at": row["logged_at"],
            "total_calories": round(total_cal, 1),
            "total_protein": round(total_prot, 1),
        })

    # Bestehenden Log laden fuer Hydration und Health-Daten
    existing_log = await db.execute(
        text("""
            SELECT hydration_water_ml, hydration_total_ml, health_data, ai_summary
            FROM daily_logs WHERE user_id = :uid AND log_date = :date
        """),
        {"uid": user_id, "date": target_date},
    )
    log_data = existing_log.mappings().first()

    return DailyLogResponse(
        log_date=target_date,
        target_nutrients=target,
        actual_nutrients=actual,
        hydration_water_ml=log_data["hydration_water_ml"] if log_data else 0,
        hydration_total_ml=log_data["hydration_total_ml"] if log_data else 0,
        caffeine_total_mg=actual.caffeine,
        alcohol_total_g=actual.alcohol,
        health_data=log_data["health_data"] if log_data else None,
        ai_summary=log_data["ai_summary"] if log_data else None,
        meals=meals,
    )


@router.get("/week")
async def get_week_overview(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Wochenrückblick: Letzte 7 Tage mit Trend-Analyse."""
    trends = await get_week_trends(user["id"], db)

    # Soll-Naehrstoffe fuer Kontext mitgeben
    user_target = user.get("target_nutrients")
    if user_target:
        if isinstance(user_target, str):
            user_target = json.loads(user_target)
        target = NutrientProfile(**user_target)
    else:
        target = calculate_target_nutrients(user)

    return {
        "start_date": trends["start_date"],
        "end_date": trends["end_date"],
        "days_tracked": trends["days_tracked"],
        "target_nutrients": target.model_dump(),
        "average_nutrients": trends["averages"],
        "chronic_deficits": trends["chronic_deficits"],
        "chronic_excesses": trends["chronic_excesses"],
    }
