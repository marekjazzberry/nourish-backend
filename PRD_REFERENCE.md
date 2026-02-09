# Nourish — PRD Referenz v1.4

> Dieses Dokument ist eine Referenz für Claude Code Teammates. Es ergänzt die CLAUDE.md um
> Design-Details, UX-Flows, Beratungston-Beispiele und Knowledge-Base-Vorgaben.

---

## 1. Kernphilosophie: "Erkenntnis vor Compliance"

Nourish erklärt nicht nur WAS, sondern WARUM. Das Ziel ist nicht blinde Befolgung von Empfehlungen,
sondern Verständnis für körperliche Prozesse.

> "Wer einmal begriffen hat, was Zucker mit seinem Schlaf macht, braucht keine App-Warnung mehr.
> Nourish macht sich langfristig selbst überflüssig — und genau das ist der Erfolg."

### Vergleich: Andere Apps vs. Nourish

| Bereich | Andere Apps | Nourish |
|---------|-------------|---------|
| Tracking | "65g Zucker heute" | "Was passiert bei 65g Zucker in deinem Körper?" |
| Warnung | Rote Ampel | "Dein Schlaf könnte heute schlechter sein, weil Zucker den Blutzucker bis in die Nacht erhöht" |
| Empfehlung | "Iss morgen weniger Zucker" | "Dein Gehirn gewöhnt sich an Zucker wie an eine Droge — in 2-3 Wochen ohne sinkt das Verlangen spürbar" |
| Langfristig | User braucht App dauerhaft | User versteht Ernährung und entscheidet eigenständig |

---

## 2. KI-Beratungston

### Grundregeln
- **Immer das WARUM erklären**, nicht nur das WAS
- **Konkreter Körperbezug**: "Dein Insulin..." statt "Zucker ist ungesund"
- **Knowledge-Base-Links** bei jedem Defizit-Hinweis: `[Mehr über THEMA]`
- **Nie verurteilend**, nie Arzt-Ton, immer warmer Freund der zufällig Ernährungswissenschaft studiert hat
- **Bei gutem Verhalten**: Fun Facts über positive Auswirkungen
- **Duzen**, nie Siezen
- **Sprache**: Deutsch

### Beispiele für Mahlzeit-Feedback

**Nach einer guten Mahlzeit:**
> "Alles klar, gespeichert! Die Walnüsse waren eine super Wahl — Omega-3 und gesunde Fette.
> Dir fehlen noch ca. 48g Protein für heute. [Mehr über Omega-3 →]"

**Nach einer zuckerhaltigen Mahlzeit:**
> "Heute war's etwas süß — dein Körper schickt gerade viel Insulin los, das kann deinen
> Schlaf heute Nacht stören. Tipp: Wenn du abends noch was isst, greif zu Protein und
> gesunden Fetten — das stabilisiert den Blutzucker. [Mehr über Zucker →]"

**Bei chronischem Defizit:**
> "Dir fehlt seit einer Woche Omega-3. Das ist einer der wichtigsten Stoffe gegen
> Entzündungen im Körper — dein Gehirn, deine Gelenke und dein Herz profitieren davon.
> Zwei Portionen Lachs pro Woche würden reichen! [Mehr über Omega-3 →]"

### Beispiele für Chat-Antworten

**User: "Warum ist Zucker eigentlich so schlecht?"**
> Zucker ist nicht per se "schlecht" — aber in den Mengen, die wir heute essen, passieren
> drei Dinge im Körper:
>
> 1. **Fruktose** (Hälfte des Haushaltszuckers) wird fast ausschließlich in der Leber verarbeitet.
>    Zu viel davon → Fettleber, ähnlich wie bei Alkohol.
> 2. **Glukosespitzen** nach dem Essen zwingen deinen Körper, massiv Insulin auszuschütten.
>    Auf Dauer → Insulinresistenz → Diabetes-Risiko.
> 3. **Dein Gehirn** reagiert auf Zucker wie auf eine Belohnung — Dopamin wird ausgeschüttet.
>    Das gleiche System wie bei Suchtmitteln.
>
> Bei dir heute: 35g Zucker, davon 20g aus Obst (ok wegen Ballaststoffe). Die restlichen 15g
> aus dem Kaffee-Sirup — da könnte man ansetzen!
>
> [Deep Dive: Zucker & Insulinresistenz →]

**User: "Und wie ist das mit dem Schlaf?"**
> Wenn du abends Zucker isst, bleibt dein Blutzucker erhöht. Dein Körper schüttet Insulin
> und Cortisol aus — beides sind Wachmacher. Studien zeigen: Menschen mit hohem Zuckerkonsum
> haben weniger Tiefschlafphasen und wachen häufiger auf.
>
> [Studie: St-Onge et al., 2016 — "Fiber and Saturated Fat Are Associated with Sleep
> Arousals and Slow Wave Sleep"]

---

## 3. App-Screens & UX

### 3.1 Home (Erfassen) — Tab 1
- Begrüßung mit personalisiertem Defizit-Hinweis ("Noch 48g Protein für heute")
- 3 animierte Ringe: Kalorien, Protein, Hydration
- Heutige Mahlzeiten als Liste mit Icons, Uhrzeit, Items, Kalorien
- **Großer grüner Mikrofon-Button** (Voice-First!)
- Sekundär: 📷 Foto, ⌨️ Text
- Nach Erfassung: AI-Feedback-Toast gleitet von unten hoch

### 3.2 Tagesbilanz — Tab 2
- 6 Makro-Ringe (Kalorien, Protein, Kohlenhydrate, Fett, Ballaststoffe, Hydration)
- **Aufmerksamkeits-Alerts**: Nur Stoffe die heute kritisch sind (< 35% oder > 120%)
- **Heatmap-Grid** für 40+ Mikronährstoffe:
  - Gruppiert: Vitamine | Vitaminähnliche | Mengenelemente | Spurenelemente | Fettsäuren
  - Farbcodiert: Rot (kritisch ≤30%) | Orange (niedrig ≤50%) | Gelb (suboptimal ≤75%) | Grün (optimal ≤110%) | Blau (hoch >110%)
  - Tap auf Kachel → **Bottom Sheet** mit Detail, Fortschrittsbalken, "Mehr erfahren"-Link
- AI-Empfehlung für nächste Mahlzeit

### 3.3 Verlauf — Tab 3
- **Kalorienbilanz-Chart**: Grüne Balken = Zufuhr, pinke Linie = Verbrauch (Apple Health)
- Balance-Label pro Tag (Defizit/Überschuss)
- Wochenzusammenfassung: Ø Zufuhr, Ø Verbrauch, Wochenbilanz
- Apple Health Schritte als Sparkline
- Protein-Trend farbcodiert
- Mikronährstoff-Trends (expandierbar)
- AI-Wochenrückblick mit Handlungsempfehlungen

### 3.4 Chat — Tab 4
- Freitext-Chat mit Nourish-KI
- Kontext: Nutzerprofil + Tagesbilanz + Wochentrends + Knowledge Base
- Voice-Input-Button in der Eingabeleiste
- Inline-Links zu Knowledge-Base-Artikeln und Studien

### 3.5 Wissen — Tab 5
- Suchleiste
- Artikel als Karten mit Icon, Titel, Preview, Effect-Tags, Studien-Badge
- **Artikel-Detail:**
  - "Kurz erklärt" Box (2-3 Sätze, alltagstauglich)
  - "Gesundheitsauswirkungen" als Karten mit Richtungspfeil, Schweregrad-Punkte
  - "Studien & Quellen" mit Evidenzlevel-Badge (Grün/Orange/Rot)

### 3.6 Profil — Tab 6
- Avatar + Name + Ernährungsform-Tags
- Geschlecht, Alter, Gewicht, Größe, Aktivitätslevel
- Ernährungseinstellungen (Diätform, Ziel, Intoleranzen)
- Verbindungen (Apple Health, Community)
- Statistiken: Streak, Einträge, Produkte

---

## 4. Knowledge Base — Inhaltsvorgaben

### 4.1 Artikelstruktur

Jeder Artikel hat zwei Ebenen:
- **Kurzfassung** (Ebene 1): 2-3 Sätze, alltagstauglich, keine Fachbegriffe
- **Deep Dive** (Ebene 2): Mechanismen, Dosierungen, Studienverweise, für Interessierte

### 4.2 Health Effects Format

Jeder Effect enthält:
- **effect_area**: z.B. diabetes, sleep, brain_fog, heart, inflammation, energy, aging, gut, immune, bone, skin, mood, weight, muscle, hormone
- **direction**: positive / negative / dose_dependent
- **severity**: mild / moderate / significant
- **short_description**: Ein Satz, verständlich
- **mechanism**: Biologischer Mechanismus (optional, für Deep Dive)
- **threshold**: Ab welcher Menge/Dauer relevant (z.B. "> 25g freier Zucker/Tag")

### 4.3 Studienreferenzen

Nur echte, verifizierbare Studien verwenden:
- **study_type**: meta_analysis > rct > cohort > review > case_study
- **evidence_level**: high (Meta-Analysen, große RCTs) / moderate (RCTs, Kohorten) / low (Einzelstudien) / preliminary (In-vitro, Piloten)
- **key_finding**: Kernaussage in einem Satz, verständlich
- Immer mit DOI oder PubMed-ID wenn verfügbar

### 4.4 Content Roadmap

**P1 (MVP):** Makronährstoffe + kritische Mikros
- Zucker (Fruktose, Glukose, Insulinresistenz)
- Omega-3 (EPA/DHA, Entzündungshemmung)
- Vitamin D (Knochen, Immunsystem, Stimmung)
- Eisen (Sauerstofftransport, Müdigkeit)
- Magnesium (Muskeln, Nerven, Schlaf)

**P2:** Erweiterte Nährstoffe + Ernährungsmuster
- Alle B-Vitamine, Vitamin C, E, K
- Calcium, Zink, Selen, Jod
- Protein-Qualität, Aminosäuren
- Keto, Intermittierendes Fasten

**P3:** Anti-Aging + Lebensmittel-Monographien
- Coenzym Q10, Alpha-Liponsäure, Carnitin
- NAD+, Sirtuine, Autophagie
- Lebensmittel-Deep-Dives (Lachs, Blaubeeren, Kurkuma...)

### 4.5 Kontextuelle Integration (6 Touchpoints)

1. **Tagesbilanz**: Tap auf Nährstoff-Kachel → Bottom Sheet → "Mehr erfahren" → Artikel
2. **KI-Feedback**: Inline-Links `[Mehr über THEMA →]` nach jeder Mahlzeit
3. **Chat**: Claude antwortet mit Knowledge-Base-Wissen + Studienverweisen
4. **Defizit-Warnung**: Push-Notification mit Artikel-Link
5. **Produkt-Detail**: Relevante Artikel zu den Nährstoffen des Produkts
6. **Wissens-Tab**: Browsebar nach Kategorien, Suche, Bookmarks

---

## 5. Nährstoffprofil — Vollständige Liste

### Makros
calories, protein, carbs, carbs_sugar, carbs_sugar_glucose, carbs_sugar_fructose, carbs_starch, fiber, fat, fat_saturated, fat_mono, fat_poly, fat_omega3, fat_omega6, fat_trans, sodium

### Vitamine (13 essenzielle)
vitamin_a (Retinol), vitamin_b1 (Thiamin), vitamin_b2 (Riboflavin), vitamin_b3 (Niacin), vitamin_b5 (Pantothensäure), vitamin_b6 (Pyridoxin), vitamin_b7 (Biotin), vitamin_b9 (Folat), vitamin_b12 (Cobalamin), vitamin_c (Ascorbinsäure), vitamin_d (Calciferol), vitamin_e (Tocopherole), vitamin_k (Phyllochinon)

### Vitaminähnliche Stoffe (7)
cholin, coenzym_q10, beta_carotin, carnitin, alpha_liponsaeure, inositol, paba

### Mengenelemente (7)
calcium, magnesium, kalium, natrium, phosphor, chlorid, schwefel

### Spurenelemente (13)
eisen, zink, kupfer, jod, selen, mangan, chrom, molybdaen, cobalt, fluorid, silizium, bor, vanadium

### Fettsäuren
omega3 (EPA, DHA, ALA), omega6

### Sonstige
caffeine, alcohol

---

## 6. Nutzer-Zielgruppe

- **Primär**: Gesundheitsbewusste 25-45, die verstehen wollen was sie essen
- **Ernährungsformen**: Pescetarisch, Keto, Vegan, etc. — App muss alle unterstützen
- **Sprache**: Deutsch (MVP), Englisch (P2)
- **Plattform**: iOS (MVP), Android (P2)

---

## 7. Technische Vorgaben für Teammates

### Claude API Calls
- **Parsing** (Voice/Text → Items): claude-sonnet-4-5-20250929, max 1024 tokens
- **Meal Feedback**: claude-sonnet-4-5-20250929, max 512 tokens, inkl. Tagesbilanz als Kontext
- **Chat**: claude-sonnet-4-5-20250929, max 2048 tokens, inkl. Profil + Bilanz + Wochentrends + KB

### System-Prompt muss immer enthalten:
1. Beratungston-Regeln (siehe Abschnitt 2)
2. Nutzerprofil (Geschlecht, Ziel, Diätform, Intoleranzen)
3. Aktuelle Tagesbilanz (Soll vs. Ist)
4. Wochentrends (7-Tage-Durchschnitt, chronische Defizite)
5. Relevante Knowledge-Base-Artikel

### Datenbank
- PostgreSQL via Supabase
- Async mit asyncpg + SQLAlchemy
- Row Level Security aktiviert
- JSONB für NutrientProfile (flexibel erweiterbar)

### API Design
- RESTful, FastAPI
- Pydantic v2 für Input/Output-Validierung
- Deutsche Fehlermeldungen in Business-Logik
- Englische Variablennamen im Code
