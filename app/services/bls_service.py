"""Nourish Backend — BLS 4.0 Fuzzy-Suche via pg_trgm."""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)


async def search_bls(name: str, db: AsyncSession, limit: int = 5) -> list[dict]:
    """Fuzzy-Suche in bls_foods via Trigram-Similarity.

    Sucht sowohl in name_de als auch name_en.
    Ranking: hoechste Similarity zuerst, bei Gleichstand kuerzerer Name.
    """
    result = await db.execute(
        text("""
            SELECT bls_code, name_de, name_en, nutrients_per_100,
                   GREATEST(
                       similarity(name_de, :q),
                       COALESCE(similarity(name_en, :q), 0)
                   ) AS sim
            FROM bls_foods
            WHERE name_de % :q OR name_en % :q
            ORDER BY sim DESC, length(name_de) ASC
            LIMIT :lim
        """),
        {"q": name, "lim": limit},
    )
    return [dict(row) for row in result.mappings()]


async def lookup_bls(name: str, db: AsyncSession) -> Optional[dict]:
    """Sucht ein Lebensmittel in der BLS-Datenbank und gibt das beste Ergebnis zurueck.

    Gibt ein dict im gleichen Format wie nutrition_service.lookup_food zurueck:
    {"name": ..., "source": "bls", "external_id": ..., "nutrients_per_100": ...}
    """
    results = await search_bls(name, db, limit=5)
    if not results:
        return None

    best = results[0]

    # Naehrstoffe aus JSONB sind bereits ein dict
    nutrients = best["nutrients_per_100"]
    if isinstance(nutrients, str):
        import json
        nutrients = json.loads(nutrients)

    return {
        "name": best["name_de"],
        "source": "bls",
        "external_id": best["bls_code"],
        "nutrients_per_100": nutrients,
    }
