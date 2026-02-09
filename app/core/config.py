"""Nourish Backend — Konfiguration über Umgebungsvariablen."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    database_url: str

    # Anthropic
    anthropic_api_key: str

    # Apple Auth
    apple_team_id: str = ""
    apple_bundle_id: str = "com.nourish.app"

    # Externe APIs
    usda_api_key: str = ""

    # App
    env: str = "development"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    # Claude Modelle
    claude_model_fast: str = "claude-sonnet-4-5-20250929"  # Parsing, schnelle Aufgaben
    claude_model_chat: str = "claude-sonnet-4-5-20250929"   # Chat, ausführliche Beratung

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
