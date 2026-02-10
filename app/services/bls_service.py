"""Nourish Backend — BLS 4.0 Suche via ILIKE mit Alias-Mapping."""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

# Exakte Alias-Mappings: Kurzformen → BLS name_de (so genau wie moeglich)
COMMON_ALIASES: dict[str, str] = {
    "ei": "Hühnerei Vollei roh",
    "eier": "Hühnerei Vollei roh",
    "spiegelei": "Hühnerei Vollei roh",
    "rührei": "Hühnerei Vollei roh",
    "avocado": "Avocado roh",
    "reis": "Reis Langkorn roh",
    "lachs": "Lachs roh",
    "milch": "Vollmilch",
    "butter": "Butter",
    "käse": "Gouda",
    "kartoffel": "Kartoffel roh",
    "kartoffeln": "Kartoffel roh",
    "tomate": "Tomate roh",
    "tomaten": "Tomate roh",
    "gurke": "Salatgurke roh",
    "apfel": "Apfel roh",
    "banane": "Banane roh",
    "hähnchen": "Hähnchenbrust roh",
    "hühnchen": "Hähnchenbrust roh",
    "huhn": "Hähnchenbrust roh",
    "rindfleisch": "Rindfleisch roh",
    "spinat": "Spinat roh",
    "brokkoli": "Brokkoli roh",
    "möhre": "Möhre roh",
    "möhren": "Möhre roh",
    "karotte": "Möhre roh",
    "karotten": "Möhre roh",
    "zwiebel": "Zwiebel roh",
    "olivenöl": "Olivenöl",
    "salat": "Kopfsalat roh",
    "brot": "Weizenmischbrot",
    "toast": "Toastbrot",
    "brötchen": "Weizenbrötchen",
    "nudeln": "Nudeln Hartweizen gegart",
    "spaghetti": "Spaghetti gegart",
    "haferflocken": "Haferflocken",
    "thunfisch": "Thunfisch roh",
    "joghurt": "Joghurt",
    "quark": "Speisequark",
    "sahne": "Sahne",
    "hackfleisch": "Hackfleisch roh",
    "schinken": "Schinken",
    "paprika": "Paprika roh",
    "orange": "Orange roh",
    "erdbeeren": "Erdbeere roh",
    "blaubeeren": "Heidelbeere roh",
    "heidelbeeren": "Heidelbeere roh",
    "mandeln": "Mandel",
    "walnüsse": "Walnuss",
    "linsen": "Linsen roh",
    "kichererbsen": "Kichererbsen roh",
    "tofu": "Tofu",
    "rapsöl": "Rapsöl",
    "pommes": "Pommes frites",
}


async def search_bls(name: str, db: AsyncSession, limit: int = 5) -> list[dict]:
    """BLS-Suche mit Alias-Mapping und Prefix-First-Strategie.

    1. Alias pruefen: exakter Kurzform-Match → expandiert zum BLS-Namen
    2. Bei Alias: Suche per Prefix (query%) — sehr praezise
    3. Ohne Alias: Suche per Prefix (query%) zuerst, dann Contains (%query%)
    """
    raw = name.strip()
    query = raw

    # 1. Alias-Mapping
    alias = COMMON_ALIASES.get(raw.lower())
    if alias:
        log.info("[BLS] Alias: '%s' → '%s'", raw, alias)
        query = alias

    # 2. Prefix-Suche zuerst (praezise, vermeidet "Ei" → "Reis")
    result = await db.execute(
        text("""
            SELECT bls_code, name_de, name_en, nutrients_per_100,
                   CASE
                       WHEN name_de ILIKE :exact THEN 1.0
                       WHEN name_de ILIKE :prefix THEN 0.9
                       WHEN name_de ILIKE :word_start THEN 0.8
                       ELSE 0.7
                   END AS sim
            FROM bls_foods
            WHERE name_de ILIKE :prefix
               OR name_de ILIKE :word_start
            ORDER BY sim DESC, length(name_de) ASC
            LIMIT :lim
        """),
        {
            "exact": query,
            "prefix": f"{query}%",
            "word_start": f"% {query}%",
            "lim": limit,
        },
    )
    rows = [dict(row) for row in result.mappings()]

    if rows:
        _log_results(raw, query, rows)
        return rows

    # 3. Fallback: Contains-Suche (breiter, aber nur wenn Prefix nichts fand)
    log.info("[BLS] Prefix ohne Treffer fuer '%s', versuche Contains", query)
    result = await db.execute(
        text("""
            SELECT bls_code, name_de, name_en, nutrients_per_100,
                   0.5 AS sim
            FROM bls_foods
            WHERE name_de ILIKE :contains
               OR name_en ILIKE :contains
            ORDER BY length(name_de) ASC
            LIMIT :lim
        """),
        {
            "contains": f"%{query}%",
            "lim": limit,
        },
    )
    rows = [dict(row) for row in result.mappings()]
    if rows:
        _log_results(raw, query, rows)
    else:
        log.warning("[BLS] Kein Treffer fuer '%s' (expandiert: '%s')", raw, query)
    return rows


def _log_results(raw: str, query: str, rows: list[dict]) -> None:
    best = rows[0]
    nutrients = best["nutrients_per_100"]
    if isinstance(nutrients, str):
        import json
        nutrients = json.loads(nutrients)
    cal = nutrients.get("calories", 0) if isinstance(nutrients, dict) else 0
    prot = nutrients.get("protein", 0) if isinstance(nutrients, dict) else 0
    log.info("[BLS] Suche '%s' (→'%s') -> Gefunden: '%s', %.0f kcal, %.1fg Protein per 100g",
             raw, query, best["name_de"], cal, prot)


async def lookup_bls(name: str, db: AsyncSession) -> Optional[dict]:
    """Sucht ein Lebensmittel in der BLS-Datenbank und gibt das beste Ergebnis zurueck."""
    results = await search_bls(name, db, limit=5)
    if not results:
        return None

    best = results[0]

    nutrients = best["nutrients_per_100"]
    if isinstance(nutrients, str):
        import json
        nutrients = json.loads(nutrients)

    log.info("[BLS] lookup '%s' → '%s' (code=%s, cal=%.0f, prot=%.1f per 100g)",
             name, best["name_de"], best["bls_code"],
             nutrients.get("calories", 0), nutrients.get("protein", 0))

    return {
        "name": best["name_de"],
        "source": "bls",
        "external_id": best["bls_code"],
        "nutrients_per_100": nutrients,
    }
