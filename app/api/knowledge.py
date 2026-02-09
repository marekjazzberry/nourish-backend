"""Nourish API — Knowledge Base (Wissensdatenbank)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.models.schemas import KnowledgeArticleListItem, KnowledgeArticleResponse

router = APIRouter()


@router.get("/", response_model=list[KnowledgeArticleListItem])
async def list_articles(
    category: str = Query(default=None),
    tag: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Wissensartikel nach Kategorie oder Tag filtern."""
    conditions = ["ka.is_published = TRUE"]
    params = {}

    if category:
        conditions.append("ka.category = :cat")
        params["cat"] = category
    if tag:
        conditions.append(":tag = ANY(ka.tags)")
        params["tag"] = tag

    where = " AND ".join(conditions)

    result = await db.execute(
        text(f"""
            SELECT ka.slug, ka.title, ka.category, ka.summary, ka.tags,
                   COUNT(DISTINCT he.id) as effects_count,
                   COUNT(DISTINCT sr.id) as studies_count
            FROM knowledge_articles ka
            LEFT JOIN health_effects he ON he.article_id = ka.id
            LEFT JOIN study_references sr ON sr.article_id = ka.id
            WHERE {where}
            GROUP BY ka.id
            ORDER BY ka.title
        """),
        params,
    )

    return [dict(row) for row in result.mappings()]


@router.get("/search", response_model=list[KnowledgeArticleListItem])
async def search_articles(
    q: str = Query(min_length=2),
    db: AsyncSession = Depends(get_db),
):
    """Volltextsuche in der Knowledge Base."""
    result = await db.execute(
        text("""
            SELECT ka.slug, ka.title, ka.category, ka.summary, ka.tags,
                   COUNT(DISTINCT he.id) as effects_count,
                   COUNT(DISTINCT sr.id) as studies_count,
                   GREATEST(
                       word_similarity(:q, ka.title),
                       word_similarity(:q, ka.summary)
                   ) as sim
            FROM knowledge_articles ka
            LEFT JOIN health_effects he ON he.article_id = ka.id
            LEFT JOIN study_references sr ON sr.article_id = ka.id
            WHERE ka.is_published = TRUE
              AND (:q <% ka.title OR :q <% ka.summary
                   OR ka.title ILIKE '%' || :q || '%'
                   OR :q = ANY(ka.tags))
            GROUP BY ka.id
            ORDER BY sim DESC
            LIMIT 20
        """),
        {"q": q},
    )

    return [dict(row) for row in result.mappings()]


@router.get("/{slug}", response_model=KnowledgeArticleResponse)
async def get_article(slug: str, db: AsyncSession = Depends(get_db)):
    """Einzelnen Wissensartikel mit Health Effects und Studien laden."""
    # Artikel
    result = await db.execute(
        text("SELECT * FROM knowledge_articles WHERE slug = :slug AND is_published = TRUE"),
        {"slug": slug},
    )
    article = result.mappings().first()
    if not article:
        raise HTTPException(404, "Artikel nicht gefunden")

    article_id = article["id"]

    # Health Effects
    effects_result = await db.execute(
        text("SELECT * FROM health_effects WHERE article_id = :aid ORDER BY sort_order"),
        {"aid": article_id},
    )
    effects = [dict(row) for row in effects_result.mappings()]

    # Studien
    studies_result = await db.execute(
        text("SELECT * FROM study_references WHERE article_id = :aid ORDER BY sort_order"),
        {"aid": article_id},
    )
    studies = [dict(row) for row in studies_result.mappings()]

    return {
        **dict(article),
        "effects": effects,
        "studies": studies,
    }
