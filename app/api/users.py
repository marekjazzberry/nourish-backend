"""Nourish API — Nutzerprofil."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.schemas import UserUpdate, UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    """Gibt das Profil des aktuellen Nutzers zurück."""
    return user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    body: UserUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Aktualisiert das Nutzerprofil.
    Bei Änderung von Körperdaten/Zielen werden target_nutrients neu berechnet.
    """
    update_fields = body.model_dump(exclude_unset=True)
    if not update_fields:
        return user

    # Dynamisches SQL bauen
    set_clauses = []
    params = {"user_id": user["id"]}
    for key, value in update_fields.items():
        set_clauses.append(f"{key} = :{key}")
        params[key] = value

    query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = :user_id RETURNING *"
    result = await db.execute(text(query), params)
    updated = result.mappings().first()
    await db.commit()

    # TODO: target_nutrients neu berechnen wenn relevante Felder geändert
    # (Gewicht, Größe, Alter, Aktivität, Ziel)

    return dict(updated)
