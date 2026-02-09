# Nourish — Backend & API

## Projektübersicht

Nourish ist eine iOS-App für intelligentes Ernährungstracking mit Voice-First UX, KI-Beratung und einer umfassenden Wissensdatenbank. Dieses Repository enthält das Backend (FastAPI + Supabase/PostgreSQL).

## Philosophie

**"Erkenntnis vor Compliance"** — Nourish erklärt nicht nur WAS, sondern WARUM. Nutzer sollen verstehen, was in ihrem Körper passiert, nicht blind Empfehlungen befolgen. Jedes KI-Feedback verbindet Tracking-Daten mit Körperverständnis.

## Tech Stack

- **API Framework:** Python FastAPI
- **Datenbank:** PostgreSQL via Supabase
- **AI:** Anthropic Claude API (claude-sonnet-4-5-20250929 für Parsing, claude-sonnet-4-5-20250929 für Chat)
- **Auth:** Apple Sign-In (JWT Verification)
- **Externe APIs:** USDA FoodData Central, Open Food Facts, BLS (German)
- **Hosting:** Supabase (DB) + Railway oder Fly.io (API)

## Projektstruktur

```
nourish-backend/
├── CLAUDE.md              ← Du bist hier
├── requirements.txt
├── .env.example
├── migrations/
│   └── 001_initial.sql    ← Komplettes DB-Schema
├── app/
│   ├── main.py            ← FastAPI App Entry
│   ├── core/
│   │   ├── config.py      ← Settings (env vars)
│   │   ├── database.py    ← Supabase/PostgreSQL connection
│   │   └── auth.py        ← Apple Sign-In verification
│   ├── models/
│   │   └── schemas.py     ← Pydantic models für alle Entities
│   ├── api/
│   │   ├── auth.py        ← POST /auth/apple
│   │   ├── users.py       ← GET/PUT /users/me
│   │   ├── meals.py       ← CRUD Mahlzeiten + Voice/Photo/Text
│   │   ├── products.py    ← Produktbibliothek + Scan
│   │   ├── daily_log.py   ← Tagesbilanz + Woche
│   │   ├── chat.py        ← POST /chat (Nourish Chat)
│   │   └── knowledge.py   ← Knowledge Base Endpunkte
│   └── services/
│       ├── claude_service.py    ← Claude API Integration
│       ├── nutrition_service.py ← USDA/OpenFoodFacts Lookup
│       ├── parsing_service.py   ← Voice/Text → strukturierte Items
│       └── balance_service.py   ← Nährstoff-Berechnung + Defizite
├── tests/
│   └── ...
└── scripts/
    └── seed_knowledge.py  ← Knowledge Base initial befüllen
```

## API-Endpunkte (MVP)

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| POST | /auth/apple | Apple Sign-In Token verifizieren |
| GET/PUT | /users/me | Nutzerprofil lesen/aktualisieren |
| POST | /meals/voice | Spracheingabe verarbeiten (Transkript) |
| POST | /meals/photo | Foto-Analyse (Mahlzeit oder Label) |
| POST | /meals/text | Text-Eingabe verarbeiten |
| GET | /meals?date=YYYY-MM-DD | Mahlzeiten für einen Tag abrufen |
| PUT | /meals/{id} | Mahlzeit bearbeiten |
| DELETE | /meals/{id} | Mahlzeit löschen |
| GET | /daily-log?date=YYYY-MM-DD | Tagesbilanz abrufen |
| GET | /daily-log/week | Wochenrückblick |
| GET/POST | /products | Persönliche Produktbibliothek |
| POST | /products/scan | Label-Scan verarbeiten |
| POST | /chat | Freitext-Chat mit Nourish-KI |
| GET | /knowledge?category=... | Wissensartikel nach Kategorie |
| GET | /knowledge/{slug} | Einzelner Wissensartikel |
| GET | /knowledge/search?q=... | Volltextsuche Knowledge Base |

## Datenmodell-Kernkonzepte

### Nutzer
- Geschlecht, Alter, Gewicht, Größe, Aktivitätslevel
- Ernährungsform (Keto, Vegan, Pescetarisch...)
- Intoleranzen (Laktose, Gluten, Histamin...)
- Gesundheitsziele (Muskelaufbau, Abnehmen, Energie...)

### Mahlzeiten
- meal_type: breakfast | lunch | dinner | snack | drink
- input_method: voice | photo | text | barcode
- Enthält FoodItems mit Referenz auf Product + berechnete Nährstoffe
- AI-Feedback wird pro Mahlzeit gespeichert

### Nährstoffprofil (JSON)
Wird in FoodItems, Products und DailyLog verwendet:
```json
{
  "calories": 385,
  "protein": 38,
  "carbs": 12, "carbs_sugar": 5, "carbs_sugar_glucose": 2, "carbs_sugar_fructose": 3, "carbs_starch": 7,
  "fiber": 8,
  "fat": 15, "fat_saturated": 3, "fat_mono": 5, "fat_poly": 6, "fat_omega3": 2.1, "fat_omega6": 3.5, "fat_trans": 0,
  "sodium": 120,
  "vitamins": { "a": 450, "b1": 0.3, "b2": 0.4, "b3": 5, "b5": 1.2, "b6": 0.5, "b7": 15, "b9": 80, "b12": 1.5, "c": 25, "d": 2, "e": 4, "k": 30 },
  "minerals": { "calcium": 200, "magnesium": 80, "potassium": 450, "phosphorus": 300, "iron": 3, "zinc": 4, "copper": 0.5, "iodine": 50, "selenium": 20, "manganese": 1.2, "chromium": 15, "molybdenum": 20 },
  "caffeine": 0,
  "alcohol": 0
}
```

### Knowledge Base
- KnowledgeArticle: Kurzfassung + Deep Dive + Tags
- HealthEffect: Strukturierte Auswirkungen (Bereich, Richtung, Schweregrad)
- StudyReference: Originalstudien mit DOI, PubMed-ID, Evidenzlevel

### Community Database
- Drei Stufen: unverified → community_verified (3+ Scans, <5% Abweichung) → expert_verified
- DSGVO-konform: Opt-in, anonymisiert, löschbar

## Claude API Prompt-Architektur

Jeder Claude-Call enthält:
1. **System-Prompt:** Beratungston (kluger Freund, nie belehrend), Erkenntnis-Fokus
2. **Nutzerkontext:** Profil, Ziele, Intoleranzen, Ernährungsform
3. **Tagesbilanz:** Aktuelle Soll/Ist-Werte aller Nährstoffe
4. **Wochentrends:** Chronische Defizite/Überschüsse (7-Tage-Schnitt)
5. **Knowledge Base:** Relevante Artikel für kontextuelle Aufklärung

### Beratungston-Regeln
- IMMER das Warum erklären, nicht nur das Was
- Konkreter Körperbezug: "Dein Insulin..." statt "Zucker ist ungesund"
- Knowledge-Base-Links bei jedem Defizit-Hinweis
- Nie verurteilend, nie Arzt-Ton, immer warmer Freund
- Bei gutem Verhalten: Fun Facts über positive Auswirkungen

## Entwicklungsreihenfolge

### Sprint 1 (Woche 1-2): Foundation
- [x] DB-Schema (diese Migration)
- [x] FastAPI Boilerplate
- [ ] Apple Auth Integration
- [ ] Basis CRUD: Users, Meals, Products

### Sprint 2 (Woche 3-4): AI Core
- [ ] Claude API: Voice-Transkript → strukturierte FoodItems
- [ ] USDA/Open Food Facts Lookup
- [ ] Nährstoff-Berechnung
- [ ] AI-Feedback nach jeder Mahlzeit

### Sprint 3 (Woche 5-6): Intelligence
- [ ] Tagesbilanz-Aggregation
- [ ] Defizit-Erkennung
- [ ] Wochentrend-Analyse
- [ ] Nourish Chat mit vollem Kontext

### Sprint 4 (Woche 7-8): Knowledge & Community
- [ ] Knowledge Base Seeding (P1-Artikel)
- [ ] Knowledge API Endpunkte
- [ ] Community Product Database
- [ ] Photo/Label Processing

## Coding-Konventionen

- Python 3.11+, Type Hints überall
- Pydantic v2 für Schemas
- async/await für alle DB-Operationen
- Fehlerbehandlung mit HTTPException + sinnvollen Messages
- Tests mit pytest + httpx (async)
- Umgebungsvariablen über .env (nie hardcoded)
- Deutsche Kommentare in Business-Logik, englische Variablennamen
