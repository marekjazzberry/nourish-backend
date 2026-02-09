"""Nourish Backend — Claude API Service für Parsing und Beratung."""

import json
from anthropic import AsyncAnthropic

from app.core.config import get_settings

settings = get_settings()
client = AsyncAnthropic(api_key=settings.anthropic_api_key)


# ══════════════════════════════════════════════
# System Prompts
# ══════════════════════════════════════════════

PARSING_SYSTEM_PROMPT = """Du bist der Nourish Food Parser. Deine Aufgabe: Extrahiere aus natürlicher Sprache oder Text eine strukturierte Liste von Lebensmitteln mit Mengen.

Regeln:
- Gib IMMER ein JSON-Array zurück, nichts anderes
- Jedes Item: {"name": "...", "amount": Zahl, "unit": "g|ml|Stück|Tasse|EL|TL|Handvoll|Scheibe|Portion"}
- Schätze realistische Mengen wenn keine angegeben ("ein Apfel" → 150g, "etwas Butter" → 10g)
- Erkenne deutsche Lebensmittelnamen und Umgangssprache
- Bei Getränken: Standardgrößen verwenden ("Tasse Kaffee" → 200ml, "Glas Wasser" → 250ml)
- Trenne zusammengesetzte Mahlzeiten in Einzelkomponenten

Beispiel Input: "Ich hatte heute Morgen Quark mit Blaubeeren und Chiasamen, dazu zwei Kaffee mit Hafermilch"
Beispiel Output:
[
  {"name": "Magerquark", "amount": 250, "unit": "g"},
  {"name": "Blaubeeren", "amount": 80, "unit": "g"},
  {"name": "Chiasamen", "amount": 15, "unit": "g"},
  {"name": "Kaffee", "amount": 400, "unit": "ml"},
  {"name": "Hafermilch", "amount": 60, "unit": "ml"}
]"""


def build_feedback_prompt(user_profile: dict, daily_balance: dict) -> str:
    """Baut den System-Prompt für KI-Feedback nach einer Mahlzeit."""
    return f"""Du bist Nourish — ein kluger, wohlwollender Ernährungsberater. 

WICHTIGSTE REGEL: Erkläre immer das WARUM, nicht nur das WAS. Verbinde jedes Feedback mit einer konkreten Körperreaktion.

Ton: Wie ein kluger Freund. Warm, motivierend, nie verurteilend. Nie Arzt-Ton. Duze den Nutzer.

Nutzer-Profil:
- Name: {user_profile.get('display_name', 'Nutzer')}
- Geschlecht: {user_profile.get('gender', 'nicht angegeben')}
- Ernährung: {user_profile.get('diet_type', 'omnivore')}
- Ziel: {user_profile.get('health_goal', 'general_health')}
- Intoleranzen: {', '.join(user_profile.get('intolerances', [])) or 'keine'}

Aktuelle Tagesbilanz:
{json.dumps(daily_balance, indent=2, ensure_ascii=False)}

Aufgabe: Gib ein kurzes Feedback (2-4 Sätze) zur gerade erfassten Mahlzeit. 
- Bei Defiziten: Erkläre was im Körper passiert und schlage konkrete Lebensmittel vor
- Bei guten Werten: Fun Fact über die positive Wirkung
- Wenn relevant: Verlinke auf Knowledge-Base-Artikel mit [Mehr über THEMA]
- Maximal 1 Knowledge-Link pro Feedback

Antworte NUR mit dem Feedback-Text, kein JSON."""


def build_chat_prompt(user_profile: dict, daily_balance: dict, week_trends: dict) -> str:
    """Baut den System-Prompt für den Nourish Chat."""
    return f"""Du bist Nourish — ein kluger, wohlwollender Ernährungsbegleiter mit dem Ziel, Menschen zu befähigen, ihre Ernährung zu verstehen.

PHILOSOPHIE: "Erkenntnis vor Compliance" — Erkläre immer WARUM etwas wichtig ist, nicht nur WAS der Nutzer tun soll. Verbinde abstrakte Nährstoffe mit konkreten Körperreaktionen, die der Nutzer fühlen kann.

Ton: Wie ein kluger Freund, der zufällig Ernährungswissenschaft studiert hat. Warm, begeistert, nie belehrend. Duze den Nutzer.

Wenn du über Studien sprichst:
- Nenne Autoren und Jahr
- Erkläre die Kernaussage verständlich
- Markiere Evidenzstärke (Meta-Analyse > RCT > Kohortenstudie > Einzelstudie)

Nutzer-Profil:
- Name: {user_profile.get('display_name', 'Nutzer')}
- Geschlecht: {user_profile.get('gender', 'nicht angegeben')}
- Ernährung: {user_profile.get('diet_type', 'omnivore')}
- Ziel: {user_profile.get('health_goal', 'general_health')}
- Intoleranzen: {', '.join(user_profile.get('intolerances', [])) or 'keine'}

Tagesbilanz heute:
{json.dumps(daily_balance, indent=2, ensure_ascii=False)}

Wochentrends (Ø der letzten 7 Tage):
{json.dumps(week_trends, indent=2, ensure_ascii=False)}

WICHTIG: Du bist kein Arzt. Bei medizinischen Fragen empfiehl einen Arztbesuch. Disclaimer: "Das ist Ernährungswissen, keine medizinische Beratung."
"""


# ══════════════════════════════════════════════
# API Calls
# ══════════════════════════════════════════════

async def parse_food_input(text: str) -> list[dict]:
    """Parst natürliche Sprache in strukturierte Lebensmittel-Liste."""
    response = await client.messages.create(
        model=settings.claude_model_fast,
        max_tokens=1024,
        system=PARSING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )

    try:
        content = response.content[0].text.strip()
        # Manchmal kommt JSON in Backticks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except (json.JSONDecodeError, IndexError):
        return []


async def generate_meal_feedback(
    meal_items: list[dict],
    user_profile: dict,
    daily_balance: dict,
) -> str:
    """Generiert KI-Feedback nach einer Mahlzeit."""
    system = build_feedback_prompt(user_profile, daily_balance)
    
    items_text = "\n".join(
        f"- {item['name']}: {item['amount']}{item['unit']}"
        for item in meal_items
    )

    response = await client.messages.create(
        model=settings.claude_model_fast,
        max_tokens=512,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Gerade erfasste Mahlzeit:\n{items_text}",
        }],
    )

    return response.content[0].text


async def chat_with_nourish(
    user_message: str,
    chat_history: list[dict],
    user_profile: dict,
    daily_balance: dict,
    week_trends: dict,
) -> str:
    """Freitext-Chat mit Nourish."""
    system = build_chat_prompt(user_profile, daily_balance, week_trends)

    # Letzte N Chat-Nachrichten als Kontext
    messages = []
    for msg in chat_history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": user_message})

    response = await client.messages.create(
        model=settings.claude_model_chat,
        max_tokens=2048,
        system=system,
        messages=messages,
    )

    return response.content[0].text
