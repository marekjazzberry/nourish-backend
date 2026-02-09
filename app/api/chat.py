"""Nourish API — Chat mit Nourish-KI."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.schemas import ChatInput, ChatResponse
from app.services.claude_service import chat_with_nourish

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    body: ChatInput,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Freitext-Chat mit Nourish — kontextbewusst mit Tagesbilanz und Wochentrends."""

    # Chat-Historie laden (letzte 10 Nachrichten)
    result = await db.execute(
        text("""
            SELECT role, content FROM chat_messages
            WHERE user_id = :uid
            ORDER BY created_at DESC LIMIT 10
        """),
        {"uid": user["id"]},
    )
    history = [dict(row) for row in reversed(list(result.mappings()))]

    # TODO: Echte Tagesbilanz und Wochentrends aus daily_logs laden
    daily_balance = {}
    week_trends = {}

    # Claude Chat
    response_text = await chat_with_nourish(
        user_message=body.message,
        chat_history=history,
        user_profile=user,
        daily_balance=daily_balance,
        week_trends=week_trends,
    )

    # Nachrichten speichern
    await db.execute(
        text("INSERT INTO chat_messages (user_id, role, content) VALUES (:uid, 'user', :content)"),
        {"uid": user["id"], "content": body.message},
    )
    await db.execute(
        text("INSERT INTO chat_messages (user_id, role, content) VALUES (:uid, 'assistant', :content)"),
        {"uid": user["id"], "content": response_text},
    )
    await db.commit()

    # TODO: Knowledge-Links aus der Antwort extrahieren
    return ChatResponse(response=response_text, knowledge_links=[])
