"""BLS 4.0 Import — Liest Excel-Daten und importiert in Supabase/PostgreSQL.

Aufruf:
    cd ~/Downloads/nourish-backend
    source venv/bin/activate
    python scripts/import_bls.py
"""

import sys
import os
import json
import asyncio
import logging

# Projekt-Root zum Path hinzufuegen (fuer app.core.config)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
import asyncpg

from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ── BLS-Code → NutrientProfile Key + optionale Einheitenkonversion ──
BLS_NUTRIENT_MAP: dict[str, tuple[str, float]] = {
    # (bls_code, (profile_key, divisor))  — divisor 1.0 = keine Konversion
    "ENERCC": ("calories", 1.0),
    "PROT625": ("protein", 1.0),
    "CHO": ("carbs", 1.0),
    "SUGAR": ("carbs_sugar", 1.0),
    "GLUS": ("carbs_sugar_glucose", 1.0),
    "FRUS": ("carbs_sugar_fructose", 1.0),
    "STARCH": ("carbs_starch", 1.0),
    "FIBT": ("fiber", 1.0),
    "FAT": ("fat", 1.0),
    "FASAT": ("fat_saturated", 1.0),
    "FAMS": ("fat_mono", 1.0),
    "FAPU": ("fat_poly", 1.0),
    "FAPUN3": ("fat_omega3", 1.0),
    "FAPUN6": ("fat_omega6", 1.0),
    "NA": ("sodium", 1.0),
    "VITA": ("vitamin_a", 1.0),
    "THIA": ("vitamin_b1", 1.0),
    "RIBF": ("vitamin_b2", 1.0),
    "NIA": ("vitamin_b3", 1.0),
    "PANTAC": ("vitamin_b5", 1.0),
    "VITB6": ("vitamin_b6", 1000.0),    # µg → mg
    "BIOT": ("vitamin_b7", 1.0),
    "FOL": ("vitamin_b9", 1.0),
    "VITB12": ("vitamin_b12", 1.0),
    "VITC": ("vitamin_c", 1.0),
    "VITD": ("vitamin_d", 1.0),
    "VITE": ("vitamin_e", 1.0),
    "VITK": ("vitamin_k", 1.0),
    "CA": ("calcium", 1.0),
    "MG": ("magnesium", 1.0),
    "K": ("potassium", 1.0),
    "P": ("phosphorus", 1.0),
    "FE": ("iron", 1.0),
    "ZN": ("zinc", 1.0),
    "CU": ("copper", 1000.0),           # µg → mg
    "ID": ("iodine", 1.0),
    "SE": ("selenium", 1.0),
    "MN": ("manganese", 1000.0),         # µg → mg
    "CR": ("chromium", 1.0),
    "MO": ("molybdenum", 1.0),
    "ALC": ("alcohol", 1.0),
}


def _build_column_index(headers: list[str]) -> dict[str, int]:
    """Baut ein Mapping: BLS-Naehrstoffcode → Spaltenindex (nur Wert-Spalte).

    Jeder Naehrstoff hat 3 Spalten: Wert, Datenherkunft, Referenz.
    Wir nehmen nur die Wert-Spalte (die erste der drei).
    """
    col_map = {}
    for idx, header in enumerate(headers):
        if not header or idx < 3:
            continue
        code = header.split()[0] if header else ""
        if "Datenherkunft" in header or "Referenz" in header:
            continue
        if code in BLS_NUTRIENT_MAP and code not in col_map:
            col_map[code] = idx
    return col_map


def _parse_value(cell_value) -> float:
    """Konvertiert einen Zellenwert in float, behandelt leere/fehlerhafte Werte."""
    if cell_value is None:
        return 0.0
    if isinstance(cell_value, (int, float)):
        return float(cell_value)
    s = str(cell_value).strip()
    if s in ("-", "", "Sp.", "Sp"):
        return 0.0
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return 0.0


def parse_excel() -> list[tuple]:
    """Liest die BLS Excel-Datei und gibt geparste Records zurueck."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "BLS_4_0_Daten_2025_DE.xlsx",
    )
    if not os.path.exists(data_path):
        log.error("BLS Daten-Datei nicht gefunden: %s", data_path)
        sys.exit(1)

    log.info("Lade BLS Excel-Datei (kann 30-60s dauern)...")
    wb = openpyxl.load_workbook(data_path, read_only=True, data_only=True)
    ws = wb.active

    rows = ws.iter_rows(values_only=True)
    header_row = next(rows)
    headers = [str(h) if h else "" for h in header_row]
    col_map = _build_column_index(headers)

    log.info("Gemappte Naehrstoffe: %d von %d", len(col_map), len(BLS_NUTRIENT_MAP))
    missing = set(BLS_NUTRIENT_MAP.keys()) - set(col_map.keys())
    if missing:
        log.warning("Nicht gefundene BLS-Codes: %s", missing)

    records = []
    for row in rows:
        bls_code = row[0]
        name_de = row[1]
        name_en = row[2] if len(row) > 2 else None

        if not bls_code or not name_de:
            continue

        bls_code = str(bls_code).strip()
        name_de = str(name_de).strip()
        name_en = str(name_en).strip() if name_en else None

        nutrients = {}
        for bls_nutrient_code, col_idx in col_map.items():
            profile_key, divisor = BLS_NUTRIENT_MAP[bls_nutrient_code]
            raw_value = row[col_idx] if col_idx < len(row) else None
            value = _parse_value(raw_value)
            if divisor != 1.0:
                value = value / divisor
            if value > 0:
                nutrients[profile_key] = round(value, 4)

        records.append((bls_code, name_de, name_en, nutrients))

    wb.close()
    log.info("Geparst: %d Lebensmittel", len(records))
    return records


async def import_to_db(records: list[tuple]):
    """Importiert geparste Records via asyncpg in die Datenbank."""
    settings = get_settings()

    # asyncpg braucht postgresql:// URL ohne SQLAlchemy-Prefix
    db_url = settings.database_url
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    db_url = db_url.replace("postgres://", "postgresql://", 1)

    conn = await asyncpg.connect(db_url)

    try:
        # pg_trgm Extension aktivieren
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

        # Tabelle erstellen
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bls_foods (
                bls_code TEXT PRIMARY KEY,
                name_de TEXT NOT NULL,
                name_en TEXT,
                nutrients_per_100 JSONB NOT NULL
            )
        """)

        # Trigram-Indizes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bls_name_de_trgm
                ON bls_foods USING gin(name_de gin_trgm_ops)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bls_name_en_trgm
                ON bls_foods USING gin(name_en gin_trgm_ops)
        """)

        log.info("Tabelle bls_foods erstellt/verifiziert")

        # Bestehende Daten loeschen (Reimport)
        await conn.execute("TRUNCATE bls_foods")

        # Batch-Insert mit asyncpg executemany
        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            await conn.executemany(
                """
                INSERT INTO bls_foods (bls_code, name_de, name_en, nutrients_per_100)
                VALUES ($1, $2, $3, $4::jsonb)
                """,
                [
                    (code, de, en, json.dumps(nutrients))
                    for code, de, en, nutrients in batch
                ],
            )
            log.info("  Importiert: %d / %d", min(i + batch_size, len(records)), len(records))

        log.info("BLS Import abgeschlossen! %d Lebensmittel in bls_foods.", len(records))

        # Sanity-Check
        count = await conn.fetchval("SELECT COUNT(*) FROM bls_foods")
        log.info("Verifizierung: %d Eintraege in bls_foods", count)

        # Beispiel: Lachs suchen
        rows = await conn.fetch("""
            SELECT bls_code, name_de, nutrients_per_100->>'protein' as protein,
                   nutrients_per_100->>'fat' as fat,
                   nutrients_per_100->>'fat_omega3' as omega3
            FROM bls_foods
            WHERE name_de ILIKE '%lachs%'
            LIMIT 5
        """)
        if rows:
            log.info("Beispiel-Suche 'Lachs':")
            for r in rows:
                log.info("  %s | %s | Protein: %s | Fett: %s | Omega-3: %s",
                         r["bls_code"], r["name_de"], r["protein"], r["fat"], r["omega3"])

    finally:
        await conn.close()


def main():
    records = parse_excel()
    asyncio.run(import_to_db(records))


if __name__ == "__main__":
    main()
