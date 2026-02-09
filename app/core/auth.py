"""Nourish Backend — Apple Sign-In Authentifizierung."""

from typing import Optional
from datetime import datetime, timezone
import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db

settings = get_settings()
security = HTTPBearer()

# Apple's öffentliche Schlüssel für JWT-Verifizierung
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
_apple_keys_cache: Optional[dict] = None


async def _get_apple_public_keys() -> dict:
    """Holt Apples öffentliche Schlüssel (mit Caching)."""
    global _apple_keys_cache
    if _apple_keys_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(APPLE_KEYS_URL)
            resp.raise_for_status()
            _apple_keys_cache = resp.json()
    return _apple_keys_cache


async def verify_apple_token(identity_token: str) -> dict:
    """
    Verifiziert ein Apple Identity Token.
    Gibt die Token-Claims zurück (sub = Apple User ID).
    """
    try:
        # Header dekodieren um den richtigen Schlüssel zu finden
        header = jwt.get_unverified_header(identity_token)
        apple_keys = await _get_apple_public_keys()

        # Passenden Schlüssel finden
        key_data = None
        for key in apple_keys.get("keys", []):
            if key["kid"] == header["kid"]:
                key_data = key
                break

        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Apple public key not found",
            )

        # Token verifizieren
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
        claims = jwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.apple_bundle_id,
            issuer="https://appleid.apple.com",
        )

        return claims

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Apple token expired",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Apple token: {e}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    FastAPI Dependency: Extrahiert und verifiziert den aktuellen Nutzer.
    Dev-Token (dev-{user_id}): User-ID direkt extrahieren.
    Produktion: Apple Identity Token verifizieren.
    """
    token = credentials.credentials

    if token.startswith("dev-"):
        # Dev-Modus: User-ID aus Token extrahieren
        user_id = token[4:]  # "dev-" abschneiden
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id},
        )
        user = result.mappings().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return dict(user)
    else:
        # Produktion: Apple Identity Token verifizieren
        claims = await verify_apple_token(token)
        apple_user_id = claims["sub"]

        from sqlalchemy import text
        result = await db.execute(
            text("SELECT * FROM users WHERE apple_user_id = :aid"),
            {"aid": apple_user_id},
        )
        user = result.mappings().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found — please register first")
        return dict(user)
