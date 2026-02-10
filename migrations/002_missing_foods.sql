-- Nourish Database Migration
-- Migration: 002_missing_foods.sql
-- Datum: 2026-02-10
-- Beschreibung: Tabelle zum Tracking von nicht-gefundenen Lebensmitteln

CREATE TABLE IF NOT EXISTS missing_foods (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    search_query TEXT NOT NULL,
    reported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved    BOOLEAN NOT NULL DEFAULT false
);

-- Index fuer schnelles Filtern nach unresolved
CREATE INDEX IF NOT EXISTS idx_missing_foods_resolved ON missing_foods (resolved) WHERE NOT resolved;

-- Deduplizierung: gleicher Name wird nicht 100x gespeichert
CREATE UNIQUE INDEX IF NOT EXISTS idx_missing_foods_name_uniq ON missing_foods (lower(name)) WHERE NOT resolved;
