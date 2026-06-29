"""
Recommendation API Routes

Provides:
1. Genre-based recommendations from TMDB.
2. TF-IDF content-based recommendations from the local dataset.
"""

from typing import List

from fastapi import APIRouter, Query

from app.schemas.schemas import TMDBMovieCard
from app.services.tmdb_services import get_genre_recommendations
from app.services.tfidf_services import tfidf_recommend_titles

router = APIRouter(
    prefix="",
    tags=["Recommendations"],
)


# =============================================================================
# Genre Recommendations
# =============================================================================

@router.get(
    "/recommend/genre",
    response_model=List[TMDBMovieCard],
    summary="Get genre-based recommendations",
    description="""
Return popular movies from the first genre of the given TMDB movie.

Workflow:
- Fetch movie details from TMDB.
- Extract the primary genre.
- Discover popular movies belonging to that genre.
- Exclude the original movie.
""",
)
async def recommend_genre(
    tmdb_id: int = Query(
        ...,
        description="TMDB movie ID",
    ),
    limit: int = Query(
        18,
        ge=1,
        le=50,
        description="Maximum number of recommendations",
    ),
):
    return await get_genre_recommendations(
        tmdb_id=tmdb_id,
        limit=limit,
    )


# =============================================================================
# TF-IDF Recommendations
# =============================================================================

@router.get(
    "/recommend/tfidf",
    summary="Get TF-IDF recommendations",
    description="""
Return content-based recommendations from the local TF-IDF model.

The input title must exist in the local dataset.
""",
)
async def recommend_tfidf(
    title: str = Query(
        ...,
        min_length=1,
        description="Movie title",
    ),
    top_n: int = Query(
        10,
        ge=1,
        le=50,
        description="Number of recommendations",
    ),
):
    recommendations = tfidf_recommend_titles(
        title,
        top_n=top_n,
    )

    return [
        {
            "title": movie_title,
            "score": score,
        }
        for movie_title, score in recommendations
    ]