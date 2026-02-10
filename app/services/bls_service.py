"""Nourish Backend — BLS 4.0 Suche via ILIKE mit Alias-Mapping."""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

# Alias-Mapping: gaengige Kurzformen/Umgangssprache → exakte BLS name_de Teilstrings
# Bei einem Alias-Treffer wird NUR nach dem Alias-Wert gesucht (kein Fallback)
_ALIASES: dict[str, str] = {
    # Eier
    "ei": "Hühnerei",
    "eier": "Hühnerei",
    "spiegelei": "Hühnerei",
    "rührei": "Hühnerei",
    # Milchprodukte
    "milch": "Vollmilch",
    "butter": "Butter",
    "käse": "Gouda",
    "joghurt": "Joghurt",
    "quark": "Speisequark",
    "sahne": "Sahne",
    "skyr": "Joghurt",
    # Getreide & Beilagen
    "reis": "Reis parboiled",
    "brot": "Weizenmischbrot",
    "toast": "Toastbrot",
    "brötchen": "Weizenbrötchen",
    "nudeln": "Nudeln Hartweizen",
    "spaghetti": "Spaghetti",
    "haferflocken": "Haferflocken",
    "kartoffel": "Kartoffel",
    "kartoffeln": "Kartoffel",
    "pommes": "Pommes frites",
    # Fleisch & Fisch
    "hähnchen": "Hähnchenbrust",
    "hühnchen": "Hähnchenbrust",
    "lachs": "Lachs",
    "thunfisch": "Thunfisch",
    "hackfleisch": "Hackfleisch",
    "schinken": "Schinken",
    "wurst": "Bratwurst",
    # Gemüse
    "tomate": "Tomate",
    "tomaten": "Tomate",
    "salat": "Kopfsalat",
    "spinat": "Spinat",
    "brokkoli": "Brokkoli",
    "gurke": "Salatgurke",
    "paprika": "Paprika",
    "zwiebel": "Zwiebel",
    "karotte": "Karotte",
    "karotten": "Karotte",
    "möhre": "Möhre",
    "möhren": "Möhre",
    # Obst
    "apfel": "Apfel",
    "banane": "Banane",
    "avocado": "Avocado",
    "orange": "Orange",
    "erdbeeren": "Erdbeere",
    "blaubeeren": "Heidelbeere",
    "heidelbeeren": "Heidelbeere",
    # Öle & Fette
    "olivenöl": "Olivenöl",
    "rapsöl": "Rapsöl",
    # Nüsse
    "mandeln": "Mandel",
    "walnüsse": "Walnuss",
    # Hülsenfrüchte
    "linsen": "Linsen",
    "kichererbsen": "Kichererbsen",
    "tofu": "Tofu",
}


async def search_bls(name: str, db: AsyncSession, limit: int = 5) -> list[dict]:
    """ILIKE-Suche in bls_foods mit Alias-Mapping und Wortgrenze-Ranking.

    1. Alias-Mapping: Kurzformen werden auf BLS-Namen expandiert
    2. ILIKE-Suche mit intelligentem Ranking:
       - Exakter Name-Match (1.0)
       - Name beginnt mit Suchbegriff (0.9)
       - Suchbegriff als ganzes Wort im Namen (0.8)
       - Suchbegriff als Wortende/Suffix (0.7)
       - Suchbegriff irgendwo enthalten (0.5)
    """
    query = name.strip()

    # Alias-Mapping anwenden
    alias = _ALIASES.get(query.lower())
    if alias:
        log.info("BLS Alias: '%s' → '%s'", query, alias)
        query = alias

    result = await db.execute(
        text("""
            SELECT bls_code, name_de, name_en, nutrients_per_100,
                   CASE
                       WHEN name_de ILIKE :exact THEN 1.0
                       WHEN name_de ILIKE :prefix THEN 0.9
                       WHEN name_de ILIKE :word_boundary THEN 0.8
                       WHEN name_de ILIKE :suffix THEN 0.7
                       WHEN name_en ILIKE :exact THEN 0.65
                       WHEN name_de ILIKE :contains THEN 0.5
                       WHEN name_en ILIKE :contains THEN 0.4
                       ELSE 0.3
                   END AS sim
            FROM bls_foods
            WHERE name_de ILIKE :contains
               OR name_en ILIKE :contains
            ORDER BY sim DESC, length(name_de) ASC
            LIMIT :lim
        """),
        {
            "exact": query,
            "prefix": f"{query}%",
            "word_boundary": f"% {query}%",
            "suffix": f"%{query}",
            "contains": f"%{query}%",
            "lim": limit,
        },
    )
    rows = [dict(row) for row in result.mappings()]
    if rows:
        log.info("BLS Treffer fuer '%s': %s (sim=%.2f)",
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
