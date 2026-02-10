"""Nourish Backend — Pydantic Schemas für alle Entities."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


# ── Enums ──

class GenderType(str, Enum):
    male = "male"
    female = "female"
    diverse = "diverse"
    prefer_not_to_say = "prefer_not_to_say"

class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"

class DietType(str, Enum):
    omnivore = "omnivore"
    pescetarian = "pescetarian"
    vegetarian = "vegetarian"
    vegan = "vegan"
    keto = "keto"
    paleo = "paleo"
    mediterranean = "mediterranean"
    other = "other"

class HealthGoal(str, Enum):
    muscle_gain = "muscle_gain"
    fat_loss = "fat_loss"
    maintenance = "maintenance"
    energy = "energy"
    longevity = "longevity"
    general_health = "general_health"

class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
    drink = "drink"

class InputMethod(str, Enum):
    voice = "voice"
    photo = "photo"
    text = "text"
    barcode = "barcode"


# ── Nährstoffprofil ──

class NutrientProfile(BaseModel):
    """Vollständiges Nährstoffprofil — wird in Products, FoodItems und DailyLog verwendet."""
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    carbs_sugar: float = 0
    carbs_sugar_glucose: float = 0
    carbs_sugar_fructose: float = 0
    carbs_starch: float = 0
    fiber: float = 0
    fat: float = 0
    fat_saturated: float = 0
    fat_mono: float = 0
    fat_poly: float = 0
    fat_omega3: float = 0
    fat_omega6: float = 0
    fat_trans: float = 0
    sodium: float = 0

    # Vitamine
    vitamin_a: float = 0      # µg
    vitamin_b1: float = 0     # mg
    vitamin_b2: float = 0     # mg
    vitamin_b3: float = 0     # mg
    vitamin_b5: float = 0     # mg
    vitamin_b6: float = 0     # mg
    vitamin_b7: float = 0     # µg
    vitamin_b9: float = 0     # µg (Folat)
    vitamin_b12: float = 0    # µg
    vitamin_c: float = 0      # mg
    vitamin_d: float = 0      # µg
    vitamin_e: float = 0      # mg
    vitamin_k: float = 0      # µg

    # Mineralstoffe
    calcium: float = 0        # mg
    magnesium: float = 0      # mg
    potassium: float = 0      # mg
    phosphorus: float = 0     # mg
    iron: float = 0           # mg
    zinc: float = 0           # mg
    copper: float = 0         # mg
    iodine: float = 0         # µg
    selenium: float = 0       # µg
    manganese: float = 0      # mg
    chromium: float = 0       # µg
    molybdenum: float = 0     # µg

    # Sonstige
    caffeine: float = 0       # mg
    alcohol: float = 0        # g


# ── User Schemas ──

class UserCreate(BaseModel):
    apple_user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    gender: Optional[GenderType] = None
    birth_date: Optional[date] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[int] = None
    activity_level: Optional[ActivityLevel] = None
    diet_type: Optional[DietType] = None
    health_goal: Optional[HealthGoal] = None
    intolerances: Optional[list[str]] = None
    health_conditions: Optional[list[str]] = None
    community_opt_in: Optional[bool] = None

class UserResponse(BaseModel):
    id: UUID
    display_name: Optional[str]
    gender: Optional[GenderType]
    birth_date: Optional[date]
    weight_kg: Optional[float]
    height_cm: Optional[int]
    activity_level: Optional[ActivityLevel]
    diet_type: Optional[DietType]
    health_goal: Optional[HealthGoal]
    intolerances: list[str] = []
    health_conditions: list[str] = []
    target_nutrients: Optional[NutrientProfile] = None
    community_opt_in: bool = False
    created_at: datetime

class AuthResponse(BaseModel):
    user: UserResponse
    token: str


# ── Meal Schemas ──

class FoodItemInput(BaseModel):
    name: str
    amount: float
    unit: str = "g"
    product_id: Optional[str] = None

class FoodItemResponse(BaseModel):
    id: UUID
    name: str
    amount: float
    unit: str
    normalized_grams: Optional[float]
    calculated_nutrients: Optional[NutrientProfile]

class VoiceInput(BaseModel):
    transcript: str
    meal_type: Optional[MealType] = None  # Auto-detect basierend auf Uhrzeit

class TextInput(BaseModel):
    text: str
    meal_type: Optional[MealType] = None

class PhotoInput(BaseModel):
    image_base64: str
    photo_type: str = "meal"  # "meal" oder "label"
    meal_type: Optional[MealType] = None

class MealUpdate(BaseModel):
    meal_type: Optional[MealType] = None
    meal_time: Optional[str] = None   # "HH:MM"
    text: Optional[str] = None        # neuer Text → Items werden neu geparst


class MealResponse(BaseModel):
    id: UUID
    meal_type: MealType
    input_method: InputMethod
    items: list[FoodItemResponse] = []
    ai_feedback: Optional[str]
    ai_feedback_knowledge_links: list[str] = []
    logged_at: datetime
    meal_time: Optional[str] = None  # "HH:MM" — wann die Mahlzeit gegessen wurde
    total_calories: float = 0
    total_protein: float = 0


# ── Product Schemas ──

class ProductCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    nutrients_per_100: NutrientProfile
    serving_size_g: Optional[float] = None
    serving_label: Optional[str] = None

class ProductResponse(BaseModel):
    id: UUID
    name: str
    brand: Optional[str]
    barcode: Optional[str]
    nutrients_per_100: NutrientProfile
    serving_size_g: Optional[float]
    serving_label: Optional[str]
    use_count: int
    last_used_at: datetime


# ── Daily Log Schemas ──

class NutrientStatus(BaseModel):
    actual: float = 0
    target: float = 0
    percentage: float = 0
    status: str = "ok"  # "deficit" | "ok" | "excess"

class DailyLogResponse(BaseModel):
    log_date: date
    target_nutrients: Optional[NutrientProfile]
    actual_nutrients: Optional[NutrientProfile]
    deficits: dict[str, NutrientStatus] = {}
    hydration_water_ml: int = 0
    hydration_total_ml: int = 0
    caffeine_total_mg: float = 0
    alcohol_total_g: float = 0
    health_data: Optional[dict] = None
    ai_summary: Optional[str]
    meals: list[MealResponse] = []


# ── Chat Schemas ──

class ChatInput(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    knowledge_links: list[str] = []


# ── Knowledge Schemas ──

class HealthEffectResponse(BaseModel):
    effect_area: str
    direction: str
    severity: str
    short_description: str
    mechanism: Optional[str]
    threshold: Optional[str]

class StudyReferenceResponse(BaseModel):
    title: str
    authors: str
    journal: str
    year: int
    doi: Optional[str]
    pubmed_id: Optional[str]
    study_type: str
    key_finding: str
    evidence_level: str

class KnowledgeArticleListItem(BaseModel):
    slug: str
    title: str
    category: str
    summary: str
    tags: list[str] = []
    effects_count: int = 0
    studies_count: int = 0

class KnowledgeArticleResponse(BaseModel):
    slug: str
    title: str
    category: str
    summary: str
    detail_html: Optional[str]
    related_nutrients: list[str] = []
    daily_recommendation: Optional[str]
    food_sources: list[str] = []
    warnings: list[str] = []
    tags: list[str] = []
    effects: list[HealthEffectResponse] = []
    studies: list[StudyReferenceResponse] = []
    last_reviewed: Optional[date]
    version: int = 1
