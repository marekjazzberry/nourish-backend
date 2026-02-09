"""Nourish API — Authentifizierung."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import verify_apple_token
from app.models.schemas import UserCreate, UserResponse

router = APIRouter()


@router.post("/apple", response_model=UserResponse)
async def apple_sign_in(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Apple Sign-In: Erstellt neuen User oder gibt existierenden zurück.
    Im Entwicklungsmodus wird das Token nicht verifiziert.
    """
    # Prüfe ob User existiert
    result = await db.execute(
        text("SELECT * FROM users WHERE apple_user_id = :aid"),
        {"aid": body.apple_user_id},
    )
    existing = result.mappings().first()

    if existing:
        return dict(existing)

    # Neuen User anlegen
    result = await db.execute(
        text("""
            INSERT INTO users (apple_user_id, email, display_name)
            VALUES (:aid, :email, :name)
            RETURNING *
        """),
        {"aid": body.apple_user_id, "email": body.email, "name": body.display_name},
    )
    user = result.mappings().first()
    await db.commit()
    return dict(user)
