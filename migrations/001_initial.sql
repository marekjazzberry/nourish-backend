-- Nourish Database Schema v1.0
-- Migration: 001_initial.sql
-- Datum: 2026-02-08
-- Beschreibung: Komplettes MVP-Schema basierend auf PRD v1.4

-- ══════════════════════════════════════════════
-- Extensions
-- ══════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Für Volltextsuche in Knowledge Base

-- ══════════════════════════════════════════════
-- Enums
-- ══════════════════════════════════════════════

CREATE TYPE gender_type AS ENUM ('male', 'female', 'diverse', 'prefer_not_to_say');
CREATE TYPE activity_level AS ENUM ('sedentary', 'light', 'moderate', 'active', 'very_active');
CREATE TYPE diet_type AS ENUM ('omnivore', 'pescetarian', 'vegetarian', 'vegan', 'keto', 'paleo', 'mediterranean', 'other');
CREATE TYPE health_goal AS ENUM ('muscle_gain', 'fat_loss', 'maintenance', 'energy', 'longevity', 'general_health');
CREATE TYPE meal_type AS ENUM ('breakfast', 'lunch', 'dinner', 'snack', 'drink');
CREATE TYPE input_method AS ENUM ('voice', 'photo', 'text', 'barcode');
CREATE TYPE verification_status AS ENUM ('unverified', 'community_verified', 'expert_verified');
CREATE TYPE knowledge_category AS ENUM ('macronutrient', 'micronutrient', 'vitamin', 'mineral', 'compound', 'habit', 'food_group', 'supplement');
CREATE TYPE effect_area AS ENUM ('diabetes', 'sleep', 'brain_fog', 'heart', 'inflammation', 'energy', 'aging', 'gut', 'immune', 'bone', 'skin', 'mood', 'weight', 'muscle', 'hormone', 'liver', 'kidney', 'eye', 'hair');
CREATE TYPE effect_direction AS ENUM ('positive', 'negative', 'neutral', 'dose_dependent');
CREATE TYPE effect_severity AS ENUM ('mild', 'moderate', 'significant');
CREATE TYPE study_type AS ENUM ('meta_analysis', 'rct', 'cohort', 'review', 'case_study', 'in_vitro');
CREATE TYPE evidence_level AS ENUM ('high', 'moderate', 'low', 'preliminary');

-- ══════════════════════════════════════════════
-- 1. Users
-- ══════════════════════════════════════════════

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    apple_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT,
    
    -- Körperdaten
    gender gender_type,
    birth_date DATE,
    weight_kg NUMERIC(5,1),
    height_cm INTEGER,
    activity_level activity_level DEFAULT 'moderate',
    
    -- Ernährungsprofil
    diet_type diet_type DEFAULT 'omnivore',
    health_goal health_goal DEFAULT 'general_health',
    intolerances TEXT[] DEFAULT '{}',  -- z.B. {'lactose', 'gluten', 'histamine'}
    health_conditions TEXT[] DEFAULT '{}',  -- z.B. {'diabetes_type2', 'hypertension'}
    
    -- Berechnete Zielwerte (werden bei Profiländerung neu berechnet)
    target_nutrients JSONB,
    
    -- Einstellungen
    language TEXT DEFAULT 'de',
    community_opt_in BOOLEAN DEFAULT FALSE,
    apple_health_connected BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_apple_id ON users(apple_user_id);

-- ══════════════════════════════════════════════
-- 2. Products (Persönliche Produktbibliothek)
-- ══════════════════════════════════════════════

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name TEXT NOT NULL,
    brand TEXT,
    barcode TEXT,
    
    -- Nährstoffprofil pro 100g/100ml
    nutrients_per_100 JSONB NOT NULL,
    serving_size_g NUMERIC(7,1),  -- Standardportion in Gramm
    serving_label TEXT,  -- z.B. "1 Becher (250g)"
    
    -- Nutzung
    use_count INTEGER DEFAULT 1,
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Community-Verknüpfung
    community_product_id UUID REFERENCES community_products(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_user ON products(user_id);
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_name_trgm ON products USING gin(name gin_trgm_ops);

-- ══════════════════════════════════════════════
-- 3. Community Products
-- ══════════════════════════════════════════════

CREATE TABLE community_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    name TEXT NOT NULL,
    brand TEXT,
    barcode TEXT UNIQUE,
    
    nutrients_per_100 JSONB NOT NULL,
    serving_size_g NUMERIC(7,1),
    serving_label TEXT,
    
    -- Verifikation
    verification_status verification_status DEFAULT 'unverified',
    scan_count INTEGER DEFAULT 1,
    confidence_score NUMERIC(3,2) DEFAULT 0.0,  -- 0.00 - 1.00
    
    -- Quellen
    source TEXT,  -- 'user_scan', 'usda', 'open_food_facts', 'bls'
    external_id TEXT,  -- ID in der externen Datenbank
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_community_barcode ON community_products(barcode);
CREATE INDEX idx_community_name_trgm ON community_products USING gin(name gin_trgm_ops);

-- ══════════════════════════════════════════════
-- 4. Product Contributions (Anonymisierte User-Beiträge)
-- ══════════════════════════════════════════════

CREATE TABLE product_contributions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_product_id UUID NOT NULL REFERENCES community_products(id) ON DELETE CASCADE,
    
    -- Anonymisiert: kein user_id, nur Hash für Deduplizierung
    contributor_hash TEXT NOT NULL,  -- SHA256(user_id + product_id)
    
    nutrients_per_100 JSONB NOT NULL,
    label_image_hash TEXT,  -- Hash des Label-Fotos (Duplikat-Erkennung)
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contributions_product ON product_contributions(community_product_id);

-- ══════════════════════════════════════════════
-- 5. Food Entries (Mahlzeiten)
-- ══════════════════════════════════════════════

CREATE TABLE food_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    meal_type meal_type NOT NULL,
    input_method input_method NOT NULL,
    
    -- Rohdaten
    raw_input TEXT,  -- Transkript, Text oder Foto-URL
    
    -- KI-Feedback
    ai_feedback TEXT,
    ai_feedback_knowledge_links TEXT[],  -- Slugs von verlinkten Knowledge-Artikeln
    
    -- Zeitstempel
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meal_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_entries_user_date ON food_entries(user_id, meal_date);
CREATE INDEX idx_entries_date ON food_entries(meal_date);

-- ══════════════════════════════════════════════
-- 6. Food Items (Einzelne Lebensmittel pro Mahlzeit)
-- ══════════════════════════════════════════════

CREATE TABLE food_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_entry_id UUID NOT NULL REFERENCES food_entries(id) ON DELETE CASCADE,
    
    -- Was
    name TEXT NOT NULL,
    product_id UUID REFERENCES products(id),
    
    -- Menge
    amount NUMERIC(7,1) NOT NULL,
    unit TEXT NOT NULL DEFAULT 'g',  -- g, ml, Stück, Tasse, EL, TL...
    normalized_grams NUMERIC(7,1),  -- Umgerechnet in Gramm
    
    -- Berechnete Nährstoffe für diese Menge
    calculated_nutrients JSONB,
    
    -- Sortierung innerhalb der Mahlzeit
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_items_entry ON food_items(food_entry_id);

-- ══════════════════════════════════════════════
-- 7. Daily Log (Tagesbilanz)
-- ══════════════════════════════════════════════

CREATE TABLE daily_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    
    -- Soll vs. Ist
    target_nutrients JSONB,  -- Snapshot der Zielwerte für diesen Tag
    actual_nutrients JSONB,  -- Summe aller Mahlzeiten
    
    -- Hydration
    hydration_water_ml INTEGER DEFAULT 0,
    hydration_total_ml INTEGER DEFAULT 0,
    caffeine_total_mg NUMERIC(6,1) DEFAULT 0,
    alcohol_total_g NUMERIC(6,1) DEFAULT 0,
    
    -- Apple Health Daten
    health_data JSONB,  -- { steps, active_calories, resting_calories, sleep_hours, weight_kg }
    
    -- KI-Zusammenfassung
    ai_summary TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, log_date)
);

CREATE INDEX idx_daily_user_date ON daily_logs(user_id, log_date);

-- ══════════════════════════════════════════════
-- 8. Knowledge Articles (Wissensdatenbank)
-- ══════════════════════════════════════════════

CREATE TABLE knowledge_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category knowledge_category NOT NULL,
    
    -- Inhalt: Zwei Ebenen
    summary TEXT NOT NULL,  -- Ebene 1: 2-3 Sätze, alltagstauglich
    detail_html TEXT,  -- Ebene 2: Deep Dive (Markdown/HTML)
    
    -- Verknüpfungen
    related_nutrients TEXT[] DEFAULT '{}',  -- z.B. {'carbs_sugar', 'fat_omega3'}
    daily_recommendation TEXT,  -- z.B. "max. 25g freier Zucker (WHO)"
    food_sources TEXT[] DEFAULT '{}',  -- z.B. {'Lachs', 'Walnüsse', 'Leinsamen'}
    warnings TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',  -- z.B. {'anti-aging', 'schlaf', 'energie'}
    
    -- Meta
    language TEXT DEFAULT 'de',
    version INTEGER DEFAULT 1,
    last_reviewed DATE,
    reviewed_by TEXT,
    is_published BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_slug ON knowledge_articles(slug);
CREATE INDEX idx_knowledge_category ON knowledge_articles(category);
CREATE INDEX idx_knowledge_tags ON knowledge_articles USING gin(tags);
CREATE INDEX idx_knowledge_nutrients ON knowledge_articles USING gin(related_nutrients);
CREATE INDEX idx_knowledge_search ON knowledge_articles USING gin(
    (title || ' ' || summary || ' ' || COALESCE(detail_html, '')) gin_trgm_ops
);

-- ══════════════════════════════════════════════
-- 9. Health Effects
-- ══════════════════════════════════════════════

CREATE TABLE health_effects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES knowledge_articles(id) ON DELETE CASCADE,
    
    effect_area effect_area NOT NULL,
    direction effect_direction NOT NULL,
    severity effect_severity NOT NULL,
    
    short_description TEXT NOT NULL,
    mechanism TEXT,
    threshold TEXT,  -- z.B. "> 25g freier Zucker/Tag"
    
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_effects_article ON health_effects(article_id);
CREATE INDEX idx_effects_area ON health_effects(effect_area);

-- ══════════════════════════════════════════════
-- 10. Study References
-- ══════════════════════════════════════════════

CREATE TABLE study_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES knowledge_articles(id) ON DELETE CASCADE,
    health_effect_id UUID REFERENCES health_effects(id) ON DELETE SET NULL,
    
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    journal TEXT NOT NULL,
    year INTEGER NOT NULL,
    
    doi TEXT,
    pubmed_id TEXT,
    url TEXT,
    
    study_type study_type NOT NULL,
    key_finding TEXT NOT NULL,
    evidence_level evidence_level NOT NULL,
    
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_studies_article ON study_references(article_id);

-- ══════════════════════════════════════════════
-- 11. Nutrition Insights (Aggregierte Kohorten-Daten)
-- ══════════════════════════════════════════════

CREATE TABLE nutrition_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Kohorte (min. 50 User, anonymisiert)
    cohort_key TEXT NOT NULL,  -- z.B. 'male_30-40_active_keto'
    cohort_size INTEGER NOT NULL CHECK (cohort_size >= 50),
    
    -- Erkenntnisse
    common_deficits JSONB,  -- z.B. [{"nutrient": "omega3", "avg_pct": 42}]
    common_excesses JSONB,
    popular_foods JSONB,
    
    -- Zeitraum
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- 12. Chat History
-- ══════════════════════════════════════════════

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    
    -- Kontext der Antwort
    knowledge_links TEXT[],  -- Slugs verlinkter Artikel
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_user ON chat_messages(user_id, created_at DESC);

-- ══════════════════════════════════════════════
-- Helper Functions
-- ══════════════════════════════════════════════

-- Auto-Update von updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers für updated_at
CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_products_updated BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_community_products_updated BEFORE UPDATE ON community_products FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_food_entries_updated BEFORE UPDATE ON food_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_daily_logs_updated BEFORE UPDATE ON daily_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_knowledge_articles_updated BEFORE UPDATE ON knowledge_articles FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ══════════════════════════════════════════════
-- Row Level Security (Supabase)
-- ══════════════════════════════════════════════

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Policies werden über Supabase Dashboard oder separate Migration konfiguriert
-- da sie vom Auth-Setup abhängen
