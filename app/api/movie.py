"""
Movie API routes.

Endpoints:
- Movie details
- Movie search bundle (Details + TF-IDF recommendations + Genre recommendations)
"""

from fastapi import APIRouter, Query

from app.schemas.schemas import (
    TMDBMovieDetails,
    SearchBundleResponse,
)
from app.services.tmdb_services import (
    get_movie_details,
    get_movie_search_bundle,
)

router = APIRouter(
    prefix="",
    tags=["Movie"],
)


# ------------ MOVIE DETAILS (SAFE ROUTE) ------------
@router.get(
    "/movie/id/{tmdb_id}",
    response_model=TMDBMovieDetails,
    summary="Get movie details",
)
async def movie_details(tmdb_id: int):
    """
    Retrieve complete details for a movie using its TMDB ID.
    """
    return await get_movie_details(tmdb_id)


# ---------- BUNDLE: Details + TF-IDF recs + Genre recs ----------
@router.get(
    "/movie/search",
    response_model=SearchBundleResponse,
    summary="Movie recommendations",
)
async def search_movie(
    query: str = Query(
        ...,
        min_length=1,
        description="Movie title",
    ),
    tfidf_top_n: int = Query(
        12,
        ge=1,
        le=30,
        description="Number of TF-IDF recommendations",
    ),
    genre_limit: int = Query(
        12,
        ge=1,
        le=30,
        description="Number of genre recommendations",
    ),
):
    """
    Returns:

    - Movie details
    - TF-IDF recommendations
    - Genre-based recommendations
    """

    return await get_movie_search_bundle(
        query=query,
        tfidf_top_n=tfidf_top_n,
        genre_limit=genre_limit,
    )