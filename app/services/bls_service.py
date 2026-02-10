"""Nourish Backend — BLS 4.0 Suche via ILIKE mit Alias-Mapping."""

import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

# Exakte Alias-Mappings: Kurzformen → verifizierte BLS name_de
# Alle Namen wurden gegen die bls_foods-Tabelle geprueft (2026-02-09)
COMMON_ALIASES: dict[str, str] = {
    # Eier (BLS: "Hühnerei roh" — 135 kcal, 13.2g P per 100g)
    "ei": "Hühnerei roh",
    "eier": "Hühnerei roh",
    "spiegelei": "Hühnerei roh",
    "rührei": "Hühnerei roh",
    "gekochtes ei": "Hühnerei gekocht",
    # Obst
    "avocado": "Avocado roh",              # 132 kcal
    "apfel": "Apfel roh",                  # 58 kcal
    "banane": "Banane roh",                # 79 kcal
    "orange": "Orange roh",                # 49 kcal
    "erdbeeren": "Erdbeere roh",           # 38 kcal
    "erdbeere": "Erdbeere roh",
    "blaubeeren": "Heidelbeere roh",       # 61 kcal
    "heidelbeeren": "Heidelbeere roh",
    # Gemüse
    "tomate": "Tomate roh",               # 22 kcal
    "tomaten": "Tomate roh",
    "gurke": "Gurke roh",                  # 16 kcal
    "kartoffel": "Kartoffel geschält, roh",  # 83 kcal
    "kartoffeln": "Kartoffel geschält, roh",
    "spinat": "Spinat roh",               # 18 kcal
    "brokkoli": "Broccoli roh",            # 35 kcal — BLS schreibt "Broccoli"!
    "broccoli": "Broccoli roh",
    "möhre": "Karotte/Möhre, roh",        # 40 kcal
    "möhren": "Karotte/Möhre, roh",
    "karotte": "Karotte/Möhre, roh",
    "karotten": "Karotte/Möhre, roh",
    "zwiebel": "Speisezwiebel roh",        # 34 kcal
    "paprika": "Gemüsepaprika rot, roh",   # 36 kcal
    "salat": "Kopfsalat roh",             # 18 kcal
    # Fleisch & Fisch
    "hähnchen": "Hähnchen Brustfilet, roh",  # 109 kcal, 23.2g P
    "hühnchen": "Hähnchen Brustfilet, roh",
    "huhn": "Hähnchen Brustfilet, roh",
    "hähnchenbrust": "Hähnchen Brustfilet, roh",
    "rindfleisch": "Rind Filet/Lende, roh",   # 121 kcal, 21.2g P
    "lachs": "Lachs roh",                      # 180 kcal, 19.9g P
    "thunfisch": "Thunfisch roh",              # 139 kcal, 22.4g P
    "hackfleisch": "Schwein/Rind, Hackfleisch gemischt, roh",  # 250 kcal
    "schinken": "Schwein Kochschinken, Kochpökelware",  # 130 kcal, 22.5g P
    # Milchprodukte
    "milch": "Vollmilch frisch, 3,5 % Fett, pasteurisiert",  # 62 kcal
    "butter": "Süßrahmbutter",             # 747 kcal
    "käse": "Gouda 48 % Fett i. Tr.",     # 379 kcal, 22.5g P
    "joghurt": "Joghurt mild, mind. 3,5 % Fett",  # 67 kcal
    "quark": "Speisequark Magerstufe, Magerquark < 10 % Fett i. Tr.",  # 66 kcal, 11.8g P
    "magerquark": "Speisequark Magerstufe, Magerquark < 10 % Fett i. Tr.",
    "sahne": "Schlagsahne mind. 30 % Fett",  # 308 kcal
    # Getreide & Beilagen
    "reis": "Reis poliert, gekocht",        # 117 kcal — gekocht ist realistischer
    "nudeln": "Teigwaren eifrei, gekocht",  # 146 kcal
    "spaghetti": "Teigwaren eifrei, gekocht",
    "pasta": "Teigwaren eifrei, gekocht",
    "brot": "Weizenmischbrot",             # 207 kcal
    "toast": "Weizenmischtoastbrot",       # 246 kcal
    "brötchen": "Weizenbrötchen",          # 280 kcal
    "haferflocken": "Hafer Flocken",       # 348 kcal, 13.2g P
    "pommes": "Pommes frites",             # 239 kcal
    # Öle & Fette
    "olivenöl": "Olivenöl",               # 899 kcal
    "rapsöl": "Rapsöl/Rüböl",             # 900 kcal
    # Hülsenfrüchte & Soja
    "linsen": "Linse reif, gekocht",       # 119 kcal — gekocht realistischer
    "kichererbsen": "Kichererbse reif, gekocht",  # 151 kcal
    "tofu": "Tofu",                        # 115 kcal, 15.5g P
    # Nüsse
    "mandeln": "Mandel süß",              # 544 kcal
    "walnüsse": "Walnuss",                # 721 kcal
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
