"""Nourish Backend — Nährstoff-Lookup über externe APIs + BLS."""

import asyncio
import logging
import aiohttp
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.schemas import NutrientProfile
from app.services.bls_service import lookup_bls

log = logging.getLogger(__name__)

settings = get_settings()

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
OFF_BASE_URL = "https://world.openfoodfacts.org/api/v2"

# Deutsche Lebensmittelnamen → englische USDA-Suchbegriffe
DE_EN_FOOD_MAP: dict[str, str] = {
    # Fleisch & Fisch
    "lachs": "salmon", "thunfisch": "tuna", "forelle": "trout",
    "kabeljau": "cod", "garnelen": "shrimp", "hering": "herring",
    "makrele": "mackerel", "sardinen": "sardines", "dorsch": "cod",
    "hähnchen": "chicken breast", "hühnchen": "chicken",
    "hähnchenbrust": "chicken breast", "hähnchenkeule": "chicken thigh",
    "putenbrust": "turkey breast", "pute": "turkey",
    "rindfleisch": "beef", "rindersteak": "beef steak",
    "hackfleisch": "ground beef", "schweinefleisch": "pork",
    "schweinefilet": "pork tenderloin", "schinken": "ham",
    "speck": "bacon", "wurst": "sausage", "bratwurst": "bratwurst sausage",
    "lamm": "lamb", "lammkeule": "lamb leg", "ente": "duck",
    # Milchprodukte
    "milch": "whole milk", "vollmilch": "whole milk",
    "magermilch": "skim milk", "buttermilch": "buttermilk",
    "joghurt": "yogurt", "naturjoghurt": "plain yogurt",
    "griechischer joghurt": "greek yogurt",
    "quark": "quark", "magerquark": "low fat quark",
    "käse": "cheese", "gouda": "gouda cheese", "emmentaler": "swiss cheese",
    "mozzarella": "mozzarella", "parmesan": "parmesan",
    "frischkäse": "cream cheese", "feta": "feta cheese",
    "butter": "butter", "sahne": "heavy cream", "schmand": "sour cream",
    "skyr": "skyr yogurt",
    # Eier
    "ei": "egg", "eier": "eggs", "spiegelei": "fried egg",
    "rührei": "scrambled eggs",
    # Getreide & Beilagen
    "reis": "rice cooked", "basmatireis": "basmati rice",
    "vollkornreis": "brown rice", "nudeln": "pasta cooked",
    "spaghetti": "spaghetti cooked", "penne": "penne pasta",
    "vollkornnudeln": "whole wheat pasta",
    "kartoffeln": "potato", "kartoffel": "potato",
    "süßkartoffel": "sweet potato", "süßkartoffeln": "sweet potato",
    "pommes": "french fries", "brot": "bread",
    "vollkornbrot": "whole wheat bread", "toast": "toast bread",
    "brötchen": "bread roll", "knäckebrot": "crispbread",
    "haferflocken": "oats", "müsli": "muesli", "cornflakes": "cornflakes",
    "couscous": "couscous", "bulgur": "bulgur", "quinoa": "quinoa",
    "hirse": "millet",
    # Hülsenfrüchte
    "linsen": "lentils", "rote linsen": "red lentils",
    "kichererbsen": "chickpeas", "bohnen": "beans",
    "kidneybohnen": "kidney beans", "schwarze bohnen": "black beans",
    "edamame": "edamame", "erbsen": "peas", "tofu": "tofu",
    "tempeh": "tempeh", "sojamilch": "soy milk",
    # Gemüse
    "spinat": "spinach", "brokkoli": "broccoli", "blumenkohl": "cauliflower",
    "karotte": "carrot", "karotten": "carrots", "möhre": "carrot",
    "möhren": "carrots", "tomate": "tomato", "tomaten": "tomatoes",
    "gurke": "cucumber", "paprika": "bell pepper",
    "zucchini": "zucchini", "aubergine": "eggplant",
    "zwiebel": "onion", "knoblauch": "garlic",
    "champignons": "mushrooms", "pilze": "mushrooms",
    "salat": "lettuce", "kopfsalat": "lettuce", "eisbergsalat": "iceberg lettuce",
    "rucola": "arugula", "grünkohl": "kale", "rosenkohl": "brussels sprouts",
    "kohlrabi": "kohlrabi", "rotkohl": "red cabbage",
    "weißkohl": "white cabbage", "sauerkraut": "sauerkraut",
    "spargel": "asparagus", "sellerie": "celery",
    "fenchel": "fennel", "lauch": "leek", "mais": "corn",
    "kürbis": "pumpkin", "süßkartoffel": "sweet potato",
    "radieschen": "radish", "rote bete": "beet",
    "erbsen": "peas", "bohnen": "green beans",
    "mangold": "swiss chard", "pak choi": "bok choy",
    "avocado": "avocado",
    # Obst
    "apfel": "apple", "banane": "banana", "orange": "orange",
    "mandarine": "tangerine", "zitrone": "lemon", "limette": "lime",
    "erdbeeren": "strawberries", "himbeeren": "raspberries",
    "blaubeeren": "blueberries", "heidelbeeren": "blueberries",
    "brombeeren": "blackberries", "johannisbeeren": "currants",
    "trauben": "grapes", "weintrauben": "grapes",
    "kirsche": "cherry", "kirschen": "cherries",
    "pfirsich": "peach", "nektarine": "nectarine",
    "pflaume": "plum", "birne": "pear",
    "mango": "mango", "ananas": "pineapple", "kiwi": "kiwi",
    "wassermelone": "watermelon", "honigmelone": "honeydew melon",
    "granatapfel": "pomegranate", "feige": "fig", "dattel": "date fruit",
    "papaya": "papaya", "maracuja": "passion fruit",
    # Nüsse & Samen
    "mandeln": "almonds", "walnüsse": "walnuts",
    "haselnüsse": "hazelnuts", "cashews": "cashew nuts",
    "erdnüsse": "peanuts", "erdnussbutter": "peanut butter",
    "pistazien": "pistachios", "paranüsse": "brazil nuts",
    "macadamia": "macadamia nuts", "pinienkerne": "pine nuts",
    "sonnenblumenkerne": "sunflower seeds", "kürbiskerne": "pumpkin seeds",
    "leinsamen": "flaxseed", "chiasamen": "chia seeds",
    "sesam": "sesame seeds", "hanfsamen": "hemp seeds",
    # Öle & Fette
    "olivenöl": "olive oil", "rapsöl": "canola oil",
    "kokosöl": "coconut oil", "sonnenblumenöl": "sunflower oil",
    "leinöl": "flaxseed oil", "sesamöl": "sesame oil",
    "margarine": "margarine",
    # Getränke
    "kaffee": "coffee brewed", "tee": "tea brewed",
    "grüner tee": "green tea", "schwarzer tee": "black tea",
    "orangensaft": "orange juice", "apfelsaft": "apple juice",
    "hafermilch": "oat milk", "mandelmilch": "almond milk",
    "kokosmilch": "coconut milk",
    # Süßes & Sonstiges
    "honig": "honey", "zucker": "sugar", "ahornsirup": "maple syrup",
    "schokolade": "chocolate", "zartbitterschokolade": "dark chocolate",
    "marmelade": "jam", "nutella": "chocolate hazelnut spread",
    "hummus": "hummus", "tahini": "tahini",
    "senf": "mustard", "ketchup": "ketchup", "mayonnaise": "mayonnaise",
    "sojasoße": "soy sauce", "essig": "vinegar",
}


# USDA Nutrient ID → unser Schema
_USDA_NUTRIENT_MAP = {
    1008: "calories", 1003: "protein", 1005: "carbs",
    1063: "carbs_sugar", 1079: "fiber", 1004: "fat",
    1258: "fat_saturated", 1292: "fat_mono", 1293: "fat_poly",
    1093: "sodium", 1087: "calcium", 1090: "magnesium",
    1092: "potassium", 1091: "phosphorus", 1089: "iron",
    1095: "zinc", 1098: "copper", 1100: "selenium",
    1101: "manganese", 1104: "vitamin_a", 1165: "vitamin_b1",
    1166: "vitamin_b2", 1167: "vitamin_b3", 1170: "vitamin_b6",
    1178: "vitamin_b12", 1162: "vitamin_c", 1114: "vitamin_d",
    1109: "vitamin_e", 1185: "vitamin_k", 1177: "vitamin_b9",
}

# Woerter die auf verarbeitete Varianten oder Nebenprodukte hindeuten
_USDA_PENALTY_WORDS = {
    "oil", "salad", "soup", "sauce", "juice", "noodle", "noodles",
    "nugget", "nuggets", "stick", "sticks", "pie", "cake", "candy",
    "cereal", "bar", "spread", "dip", "mix", "baby", "infant",
    "powder", "supplement", "extract", "dried", "dehydrated",
    "lomi", "jerky", "pickled", "cured", "chip", "chips",
}


async def search_usda(query: str, max_results: int = 10, _retries: int = 3) -> list[dict]:
    """Sucht Lebensmittel in der USDA FoodData Central Datenbank (mit Retry)."""
    if not settings.usda_api_key:
        return []

    for attempt in range(_retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": settings.usda_api_key,
                    "query": query,
                    "pageSize": max_results,
                    "dataType": ["Survey (FNDDS)", "Foundation", "SR Legacy"],
                }
                async with session.get(f"{USDA_BASE_URL}/foods/search", params=params) as resp:
                    if resp.status != 200:
                        # USDA gibt 400 bei Rate-Limiting (statt 429)
                        log.warning("USDA API %s fuer '%s' (Versuch %d/%d)",
                                    resp.status, query, attempt + 1, _retries + 1)
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    data = await resp.json(content_type=None)
                    return _parse_usda_results(data.get("foods", []))
        except (aiohttp.ClientError, ValueError, KeyError) as e:
            log.warning("USDA Fehler fuer '%s': %s (Versuch %d/%d)",
                        query, e, attempt + 1, _retries + 1)
            await asyncio.sleep(1.0 * (attempt + 1))
            continue
    log.error("USDA Lookup gescheitert fuer '%s' nach %d Versuchen", query, _retries + 1)
    return []


def _rank_usda_result(food: dict, query: str) -> float:
    """Bewertet ein USDA-Ergebnis nach Relevanz fuer die Suchanfrage."""
    desc = food.get("description", "").lower()
    query_lower = query.lower()
    score = 0.0

    # Basis-Score von USDA uebernehmen (normalisiert)
    score += min(food.get("score", 0) / 1000.0, 1.0)

    # Exakter Match des Suchbegriffs am Anfang der Beschreibung (z.B. "Spinach, raw")
    first_word = desc.split(",")[0].strip()
    query_words = query_lower.split()
    if first_word == query_lower or first_word in query_words:
        score += 5.0

    # "cooked" oder "raw" Variante bevorzugen (echte Grundlebensmittel)
    if "cooked" in desc and "cooked" not in query_lower:
        score += 3.0
    if "raw" in desc:
        score += 2.0

    # NFS = "Not Further Specified" — guter generischer Treffer
    if "nfs" in desc.lower():
        score += 2.5

    # Survey (FNDDS) bevorzugen — generische, gut gepflegte Daten
    dtype = food.get("dataType", "")
    if dtype == "Survey (FNDDS)":
        score += 1.5
    elif dtype == "SR Legacy":
        score += 1.0

    # Beschreibung beginnt mit dem Suchbegriff
    if desc.startswith(query_lower):
        score += 2.0

    # Penalty fuer verarbeitete Produkte / Nebenprodukte
    desc_words = set(desc.replace(",", " ").split())
    penalties = desc_words & _USDA_PENALTY_WORDS
    score -= len(penalties) * 3.0

    # Penalty fuer sehr lange Beschreibungen (meist spezifische Rezepte)
    if len(desc) > 80:
        score -= 1.0

    return score


def _parse_usda_results(foods: list[dict]) -> list[dict]:
    """Konvertiert USDA-Ergebnisse in ein einheitliches Format."""
    results = []
    for food in foods:
        nutrients = {}
        for n in food.get("foodNutrients", []):
            nutrient_id = n.get("nutrientId")
            value = n.get("value", 0)
            if nutrient_id in _USDA_NUTRIENT_MAP:
                nutrients[_USDA_NUTRIENT_MAP[nutrient_id]] = value

        results.append({
            "name": food.get("description", ""),
            "source": "usda",
            "external_id": str(food.get("fdcId", "")),
            "nutrients_per_100": nutrients,
            "_raw": food,  # Fuer Ranking benoetigt
        })
    return results


async def search_open_food_facts(barcode: str) -> Optional[dict]:
    """Sucht ein Produkt per Barcode in Open Food Facts."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{OFF_BASE_URL}/product/{barcode}") as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

            if data.get("status") != 1:
                return None

            product = data.get("product", {})
            nutriments = product.get("nutriments", {})

            return {
                "name": product.get("product_name", "Unbekanntes Produkt"),
                "brand": product.get("brands", ""),
                "barcode": barcode,
                "source": "open_food_facts",
                "nutrients_per_100": {
                    "calories": nutriments.get("energy-kcal_100g", 0),
                    "protein": nutriments.get("proteins_100g", 0),
                    "carbs": nutriments.get("carbohydrates_100g", 0),
                    "carbs_sugar": nutriments.get("sugars_100g", 0),
                    "fiber": nutriments.get("fiber_100g", 0),
                    "fat": nutriments.get("fat_100g", 0),
                    "fat_saturated": nutriments.get("saturated-fat_100g", 0),
                    "sodium": nutriments.get("sodium_100g", 0) * 1000,  # g → mg
                    "vitamin_c": nutriments.get("vitamin-c_100g", 0),
                    "calcium": nutriments.get("calcium_100g", 0) * 1000,
                    "iron": nutriments.get("iron_100g", 0) * 1000,
                },
            }


def _translate_food_name(name: str) -> Optional[str]:
    """Übersetzt einen deutschen Lebensmittelnamen ins Englische für USDA."""
    key = name.lower().strip()
    if key in DE_EN_FOOD_MAP:
        return DE_EN_FOOD_MAP[key]
    # Teilwort-Suche: "gebratener Lachs" → "Lachs" → "salmon"
    for de, en in DE_EN_FOOD_MAP.items():
        if de in key or key in de:
            return en
    return None


def _pick_best_result(results: list[dict], query: str) -> Optional[dict]:
    """Waehlt das beste USDA-Ergebnis anhand von Relevanz-Ranking."""
    if not results:
        return None
    ranked = sorted(
        results,
        key=lambda r: _rank_usda_result(r.get("_raw", {}), query),
        reverse=True,
    )
    best = ranked[0]
    best.pop("_raw", None)
    # Auch _raw aus den anderen entfernen (Memory)
    for r in ranked[1:]:
        r.pop("_raw", None)
    return best


# Globaler Timestamp fuer Rate-Limit-Schutz
_last_usda_call: float = 0.0
_USDA_MIN_INTERVAL = 0.4  # Sekunden zwischen USDA-Anfragen


async def _throttled_search_usda(query: str, max_results: int = 10) -> list[dict]:
    """USDA-Suche mit Throttling zum Schutz vor Rate-Limiting."""
    global _last_usda_call
    import time
    now = time.monotonic()
    wait = _USDA_MIN_INTERVAL - (now - _last_usda_call)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_usda_call = time.monotonic()
    return await search_usda(query, max_results)


async def _log_missing_food(name: str, search_query: str, db: Optional[AsyncSession]) -> None:
    """Speichert ein nicht-gefundenes Lebensmittel in missing_foods."""
    if db is None:
        return
    try:
        from sqlalchemy import text as sa_text
        await db.execute(
            sa_text("""
                INSERT INTO missing_foods (name, search_query)
                VALUES (:name, :query)
                ON CONFLICT (lower(name)) WHERE NOT resolved DO NOTHING
            """),
            {"name": name, "query": search_query},
        )
        log.warning("[MISSING] Lebensmittel nicht gefunden: '%s' (query: '%s')", name, search_query)
    except Exception as e:
        log.error("[MISSING] Fehler beim Speichern: %s", e)


async def lookup_food(
    name: str, db: Optional[AsyncSession] = None, barcode: Optional[str] = None,
) -> Optional[dict]:
    """
    Sucht ein Lebensmittel — Reihenfolge:
    1. Barcode → Open Food Facts (exakt)
    2. BLS 4.0 → Fuzzy-Suche (primaer, schnell, deutsche Daten)
    3. USDA → Fallback (englisch, mit Uebersetzung)
    4. Nicht gefunden → in missing_foods loggen
    """
    # 1. Barcode-Suche (exakt)
    if barcode:
        result = await search_open_food_facts(barcode)
        if result:
            return result

    # 2. BLS-Suche (primaer fuer deutsche Lebensmittel)
    if db is not None:
        bls_result = await lookup_bls(name, db)
        if bls_result:
            log.info("BLS Treffer fuer '%s': %s", name, bls_result["name"])
            return bls_result

    # 3. Deutschen Namen uebersetzen (falls moeglich)
    translated = _translate_food_name(name)
    search_name = translated if translated else name

    # 4. USDA-Suche mit mehreren Ergebnissen + Ranking (throttled)
    results = await _throttled_search_usda(search_name, max_results=10)
    best = _pick_best_result(results, search_name)
    if best:
        return best

    # 5. Fallback: Originalname versuchen (falls Uebersetzung fehlschlug)
    if translated and translated.lower() != name.lower():
        results = await _throttled_search_usda(name, max_results=10)
        best = _pick_best_result(results, name)
        if best:
            return best

    # 6. Nichts gefunden → in missing_foods loggen
    await _log_missing_food(name, search_name, db)
    return None


def calculate_nutrients(nutrients_per_100: dict, amount_grams: float, food_name: str = "") -> NutrientProfile:
    """Berechnet Nährstoffe für eine bestimmte Menge basierend auf per-100g-Werten."""
    factor = amount_grams / 100.0
    calculated = {}
    for key, value in nutrients_per_100.items():
        if isinstance(value, (int, float)):
            calculated[key] = round(value * factor, 2)

    cal = calculated.get("calories", 0)
    prot = calculated.get("protein", 0)
    carbs = calculated.get("carbs", 0)
    fat = calculated.get("fat", 0)
    log.info("[CALC] %s: %.0fg → %.0f kcal, %.1fg P, %.1fg C, %.1fg F (factor=%.2f)",
             food_name or "?", amount_grams, cal, prot, carbs, fat, factor)

    return NutrientProfile(**calculated)
