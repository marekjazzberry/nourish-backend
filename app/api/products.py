"""Nourish API — Produktbibliothek."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.schemas import ProductCreate, ProductResponse

router = APIRouter()


@router.get("", response_model=list[ProductResponse])
async def list_products(
    search: str = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alle persönlichen Produkte, optional mit Suche."""
    if search:
        result = await db.execute(
            text("""
                SELECT * FROM products
                WHERE user_id = :uid AND name ILIKE :search
                ORDER BY use_count DESC LIMIT 50
            """),
            {"uid": user["id"], "search": f"%{search}%"},
        )
    else:
        result = await db.execute(
            text("SELECT * FROM products WHERE user_id = :uid ORDER BY use_count DESC LIMIT 100"),
            {"uid": user["id"]},
        )
    return [dict(row) for row in result.mappings()]


@router.post("", response_model=ProductResponse)
async def create_product(
    body: ProductCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Neues Produkt zur persönlichen Bibliothek hinzufügen."""
    result = await db.execute(
        text("""
            INSERT INTO products (user_id, name, brand, barcode, nutrients_per_100, serving_size_g, serving_label)
            VALUES (:uid, :name, :brand, :barcode, :nutrients, :serving_g, :serving_label)
            RETURNING *
        """),
        {
            "uid": user["id"], "name": body.name, "brand": body.brand,
            "barcode": body.barcode, "nutrients": body.nutrients_per_100.model_dump_json(),
            "serving_g": body.serving_size_g, "serving_label": body.serving_label,
        },
    )
    product = result.mappings().first()
    await db.commit()
    return dict(product)
