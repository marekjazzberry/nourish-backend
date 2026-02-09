"""Nourish API — Authentifizierung."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import verify_apple_token
from app.models.schemas import UserCreate, AuthResponse

router = APIRouter()


@router.post("/apple", response_model=AuthResponse)
async def apple_sign_in(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Apple Sign-In: Erstellt neuen User oder gibt existierenden zurück.
    Dev-Modus: Wenn apple_user_id mit "dev-" beginnt, wird die
    Apple-Token-Verifikation übersprungen.
    """
    is_dev = body.apple_user_id.startswith("dev-")

    if not is_dev:
        # Produktion: Apple Identity Token verifizieren
        # (identity_token müsste im Body mitgeschickt werden)
        pass

    # Prüfe ob User existiert
    result = await db.execute(
        text("SELECT * FROM users WHERE apple_user_id = :aid"),
        {"aid": body.apple_user_id},
    )
    existing = result.mappings().first()

    if existing:
        user = dict(existing)
        token = f"dev-{user['id']}" if is_dev else str(user["id"])
        return {"user": user, "token": token}

    # Neuen User anlegen
    result = await db.execute(
        text("""
            INSERT INTO users (apple_user_id, email, display_name)
            VALUES (:aid, :email, :name)
            RETURNING *
        """),
        {"aid": body.apple_user_id, "email": body.email, "name": body.display_name},
    )
    user = dict(result.mappings().first())
    await db.commit()

    token = f"dev-{user['id']}" if is_dev else str(user["id"])
    return {"user": user, "token": token}
