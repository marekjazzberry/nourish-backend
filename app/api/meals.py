"""Nourish API — Mahlzeiten erfassen und verwalten."""

import json as json_mod
from datetime import date as date_type, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.schemas import (
    VoiceInput, TextInput, PhotoInput, MealResponse, MealType, NutrientProfile,
)
from app.services.claude_service import parse_food_input, generate_meal_feedback
from app.services.nutrition_service import lookup_food, calculate_nutrients

router = APIRouter()


async def _process_meal(
    parsed_items: list[dict],
    meal_type: MealType,
    input_method: str,
    raw_input: str,
    user: dict,
    db: AsyncSession,
) -> MealResponse:
    """Gemeinsame Logik für alle Eingabemethoden."""

    # 1. Mahlzeit-Eintrag erstellen
    result = await db.execute(
        text("""
            INSERT INTO food_entries (user_id, meal_type, input_method, raw_input, meal_date)
            VALUES (:uid, :mt, :im, :raw, :date)
            RETURNING id, logged_at
        """),
        {
            "uid": user["id"], "mt": meal_type.value,
            "im": input_method, "raw": raw_input,
            "date": date_type.today(),
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
        normalized_grams = item["amount"]  # Vereinfachung für MVP

        if food_data and "nutrients_per_100" in food_data:
            nutrients = calculate_nutrients(
                food_data["nutrients_per_100"], normalized_grams
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
        total_calories=total_cal,
        total_protein=total_prot,
    )


def _detect_meal_type() -> MealType:
    """Erkennt den Mahlzeittyp basierend auf der Uhrzeit."""
    hour = datetime.now().hour
    if hour < 10:
        return MealType.breakfast
    elif hour < 14:
        return MealType.lunch
    elif hour < 17:
        return MealType.snack
    else:
        return MealType.dinner


@router.post("/voice", response_model=MealResponse)
async def create_meal_voice(
    body: VoiceInput,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verarbeitet Spracheingabe → Mahlzeit."""
    parsed_items = await parse_food_input(body.transcript)
    if not parsed_items:
        raise HTTPException(400, "Konnte keine Lebensmittel erkennen. Bitte nochmal versuchen.")

    meal_type = body.meal_type or _detect_meal_type()
    return await _process_meal(parsed_items, meal_type, "voice", body.transcript, user, db)


@router.post("/text", response_model=MealResponse)
async def create_meal_text(
    body: TextInput,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verarbeitet Texteingabe → Mahlzeit."""
    parsed_items = await parse_food_input(body.text)
    if not parsed_items:
        raise HTTPException(400, "Konnte keine Lebensmittel erkennen.")

    meal_type = body.meal_type or _detect_meal_type()
    return await _process_meal(parsed_items, meal_type, "text", body.text, user, db)


@router.get("/", response_model=list[MealResponse])
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

        meals.append(MealResponse(
            id=row["id"],
            meal_type=row["meal_type"],
            input_method=row["input_method"],
            items=parsed_items,
            ai_feedback=row["ai_feedback"],
            ai_feedback_knowledge_links=row["ai_feedback_knowledge_links"] or [],
            logged_at=row["logged_at"],
            total_calories=round(total_cal, 1),
            total_protein=round(total_prot, 1),
        ))

    return meals


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
