"""Nourish Backend — Datenbankverbindung (Supabase/PostgreSQL)."""

import re
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from supabase import create_client, Client

from app.core.config import get_settings

settings = get_settings()

# ── SQLAlchemy Async Engine (für direkte DB-Operationen) ──
_engine = None
_session_factory = None


def _make_psycopg_url(url: str) -> str:
    """Konvertiert eine beliebige PostgreSQL-URL zum psycopg-Driver-Format."""
    return re.sub(
        r"^postgres(ql)?(\+\w+)?://",
        "postgresql+psycopg://",
        url,
    )


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _make_psycopg_url(settings.database_url),
            echo=settings.debug,
            poolclass=NullPool,
        )
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_db() -> AsyncSession:
    """FastAPI Dependency: liefert eine DB-Session pro Request."""
    async with _get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Supabase Client (für Auth und Storage) ──
def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)
