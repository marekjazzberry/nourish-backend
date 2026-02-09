"""Nourish Backend — FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import auth, users, meals, products, daily_log, chat, knowledge

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/Shutdown Events."""
    # Startup
    print("🌿 Nourish Backend starting...")
    yield
    # Shutdown
    print("🌿 Nourish Backend shutting down...")


app = FastAPI(
    title="Nourish API",
    description="Intelligentes Ernährungstracking mit KI-Beratung",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router einbinden
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(meals.router, prefix="/meals", tags=["Meals"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(daily_log.router, prefix="/daily-log", tags=["Daily Log"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nourish-api", "version": "0.1.0"}
