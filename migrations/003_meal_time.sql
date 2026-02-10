-- Nourish Database Migration
-- Migration: 003_meal_time.sql
-- Datum: 2026-02-10
-- Beschreibung: meal_time Spalte fuer chronologische Sortierung

ALTER TABLE food_entries ADD COLUMN IF NOT EXISTS meal_time TIME;

-- Bestehende Eintraege: meal_time aus logged_at ableiten
UPDATE food_entries SET meal_time = logged_at::time WHERE meal_time IS NULL;

-- Index fuer chronologische Sortierung
CREATE INDEX IF NOT EXISTS idx_food_entries_meal_time ON food_entries (user_id, meal_date, meal_time);
