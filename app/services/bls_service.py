"""Nourish Backend — BLS 4.0 Fuzzy-Suche via pg_trgm."""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

# Kurzform-Mapping: gaengige Kurzformen → besserer BLS-Suchbegriff
# Wird VOR der Trigram-/ILIKE-Suche angewendet
_SHORT_FORM_MAP: dict[str, str] = {
    "ei": "Hühnerei",
    "eier": "Hühnerei",
    "reis": "Reis parboiled",
    "milch": "Vollmilch",
    "brot": "Weizenmischbrot",
    "butter": "Butter",
    "käse": "Gouda",
    "lachs": "Lachs",
    "kartoffel": "Kartoffel gegart",
    "kartoffeln": "Kartoffel gegart",
    "tomate": "Tomate",
    "tomaten": "Tomate",
    "salat": "Kopfsalat",
    "spinat": "Spinat",
    "brokkoli": "Brokkoli",
    "hähnchen": "Hähnchenbrust",
    "hühnchen": "Hähnchenbrust",
    "thunfisch": "Thunfisch",
    "joghurt": "Joghurt",
    "quark": "Speisequark",
    "nudeln": "Nudeln Hartweizen gegart",
    "spaghetti": "Spaghetti gegart",
    "haferflocken": "Haferflocken",
    "apfel": "Apfel",
    "banane": "Banane",
    "avocado": "Avocado",
    "olivenöl": "Olivenöl",
}


async def search_bls(name: str, db: AsyncSession, limit: int = 5) -> list[dict]:
    """Fuzzy-Suche in bls_foods via Trigram-Similarity.

    Sucht sowohl in name_de als auch name_en.
    Ranking: hoechste Similarity zuerst, bei Gleichstand kuerzerer Name.

    Bei kurzen Suchbegriffen und Kurzformen wird zuerst ein Mapping geprueft,
    dann Trigram-Suche, und als Fallback ILIKE.
    """
    query = name.strip()

    # Kurzform-Mapping anwenden
    expanded = _SHORT_FORM_MAP.get(query.lower())
    if expanded:
        log.info("BLS Kurzform-Mapping: '%s' → '%s'", query, expanded)
        query = expanded

    # Trigram-Suche
    result = await db.execute(
        text("""
            SELECT bls_code, name_de, name_en, nutrients_per_100,
                   GREATEST(
                       similarity(name_de, :q),
                       COALESCE(similarity(name_en, :q), 0)
                   ) AS sim
            FROM bls_foods
            WHERE name_de %% :q OR name_en %% :q
            ORDER BY sim DESC, length(name_de) ASC
            LIMIT :lim
        """),
        {"q": query, "lim": limit},
    )
    rows = [dict(row) for row in result.mappings()]

    if rows:
        log.info("BLS Trigram-Treffer fuer '%s': %s (sim=%.2f)",
                 query, rows[0]["name_de"], rows[0]["sim"])
        return rows

    # Fallback: ILIKE fuer Begriffe die Trigram nicht findet
    log.info("BLS Trigram ohne Treffer fuer '%s', versuche ILIKE-Fallback", query)
    result = await db.execute(
        text("""
            SELECT bls_code, name_de, name_en, nutrients_per_100,
                   CASE
                       WHEN name_de ILIKE :exact THEN 1.0
                       WHEN name_de ILIKE :suffix THEN 0.9
                       WHEN name_de ILIKE :prefix THEN 0.8
                       WHEN name_de ILIKE :contains THEN 0.7
                       WHEN name_en ILIKE :contains THEN 0.6
                       ELSE 0.5
                   END AS sim
            FROM bls_foods
            WHERE name_de ILIKE :contains
               OR name_en ILIKE :contains
            ORDER BY sim DESC, length(name_de) ASC
            LIMIT :lim
        """),
        {
            "exact": query,
            "suffix": f"%{query}",
            "prefix": f"{query}%",
            "contains": f"%{query}%",
            "lim": limit,
        },
    )
    rows = [dict(row) for row in result.mappings()]
    if rows:
        log.info("BLS ILIKE-Treffer fuer '%s': %s (sim=%.2f)",
                 query, rows[0]["name_de"], rows[0]["sim"])
    else:
        log.warning("BLS kein Treffer fuer '%s'", query)
    return rows


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

    log.info("BLS lookup '%s' → '%s' (code=%s, cal=%.0f, prot=%.1f per 100g)",
             name, best["name_de"], best["bls_code"],
             nutrients.get("calories", 0), nutrients.get("protein", 0))

    return {
        "name": best["name_de"],
        "source": "bls",
        "external_id": best["bls_code"],
        "nutrients_per_100": nutrients,
    }
