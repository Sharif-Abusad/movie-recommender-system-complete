"""
TMDB service layer.

Responsible for:
- Communicating with the TMDB API
- Searching movies
- Fetching movie details
- Building lightweight movie cards
- Genre-based recommendations
"""

from typing import Any, Dict, List, Optional, Tuple

import asyncio
import httpx
from fastapi import HTTPException, Query

from app.schemas.schemas import (
    TFIDFRecommendation,
    SearchBundleResponse
)

from app.services.tfidf_services import (
    tfidf_recommend_titles, 
    
)
from app.core.config import (
    TMDB_API_KEY,
    TMDB_BASE,
    TMDB_IMAGE_BASE_URL,
)
from app.core.state import state
from app.schemas.schemas import (
    TMDBMovieCard,
    TMDBMovieDetails,
)

# ==========================================================
# Private Helpers
# ==========================================================


def _make_image_url(path: Optional[str]) -> Optional[str]:
    """
    Convert TMDB image path to a full image URL.
    """
    if not path:
        return None

    return f"{TMDB_IMAGE_BASE_URL}{path}"


# ==========================================================
# TMDB HTTP Client
# ==========================================================


async def tmdb_get(
    path: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Perform a GET request to the TMDB API.

    Features
    --------
    - Automatic retries
    - Exponential backoff
    - Proper HTTPException conversion
    """

    query = dict(params)
    query["api_key"] = TMDB_API_KEY

    last_error: Optional[Exception] = None

    for attempt in range(3):

        try:
            response = await state.client.get(
                f"{TMDB_BASE}{path}",
                params=query,
            )

            response.raise_for_status()

            return response.json()

        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.RemoteProtocolError,
        ) as exc:

            last_error = exc

            wait = 2 ** attempt

            print(
                f"[TMDB] Attempt {attempt + 1}/3 failed "
                f"({type(exc).__name__}). "
                f"Retrying in {wait}s..."
            )

            await asyncio.sleep(wait)

        except httpx.HTTPStatusError as exc:

            raise HTTPException(
                status_code=502,
                detail=f"TMDB returned {exc.response.status_code}: {exc.response.text}",
            )

    raise HTTPException(
        status_code=502,
        detail=f"TMDB unreachable after 3 attempts ({type(last_error).__name__})",
    )


# ==========================================================
# Search
# ==========================================================


async def tmdb_search_movies(
    query: str,
    page: int = 1,
) -> Dict[str, Any]:
    """
    Search TMDB for movies.
    """

    return await tmdb_get(
        "/search/movie",
        {
            "query": query,
            "language": "en-US",
            "include_adult": False,
            "page": page,
        },
    )


async def tmdb_search_first(
    query: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the first search result.
    """

    data = await tmdb_search_movies(query)

    results = data.get("results", [])

    return results[0] if results else None


# ==========================================================
# Movie Details
# ==========================================================


async def get_movie_details(
    movie_id: int,
) -> TMDBMovieDetails:
    """
    Fetch detailed information for a movie.
    """

    data = await tmdb_get(
        f"/movie/{movie_id}",
        {"language": "en-US"},
    )

    return TMDBMovieDetails(
        tmdb_id=int(data["id"]),
        title=data.get("title", ""),
        overview=data.get("overview"),
        release_date=data.get("release_date"),
        poster_url=_make_image_url(data.get("poster_path")),
        backdrop_url=_make_image_url(data.get("backdrop_path")),
        genres=data.get("genres", []),
    )


# ==========================================================
# Card Builders
# ==========================================================


async def tmdb_cards_from_results(
    results: List[Dict[str, Any]],
    limit: int = 20,
) -> List[TMDBMovieCard]:
    """
    Convert TMDB search results into movie cards.
    """

    cards: List[TMDBMovieCard] = []

    for movie in results[:limit]:

        cards.append(
            TMDBMovieCard(
                tmdb_id=int(movie["id"]),
                title=movie.get("title") or movie.get("name", ""),
                poster_url=_make_image_url(movie.get("poster_path")),
                release_date=movie.get("release_date"),
                vote_average=movie.get("vote_average"),
            )
        )

    return cards


async def attach_tmdb_card_by_title(
    title: str,
) -> Optional[TMDBMovieCard]:
    """
    Search TMDB by title and return a lightweight movie card.
    """

    try:

        movie = await tmdb_search_first(title)

        if movie is None:
            return None

        return TMDBMovieCard(
            tmdb_id=int(movie["id"]),
            title=movie.get("title", title),
            poster_url=_make_image_url(movie.get("poster_path")),
            release_date=movie.get("release_date"),
            vote_average=movie.get("vote_average"),
        )

    except HTTPException:
        return None


# ==========================================================
# Recommendations
# ==========================================================


async def get_genre_recommendations(
    tmdb_id: int,
    limit: int = 20,
) -> List[TMDBMovieCard]:
    """
    Recommend popular movies from the first genre of the movie.
    """

    details = await get_movie_details(tmdb_id)

    if not details.genres:
        return []

    genre_id = details.genres[0]["id"]

    data = await tmdb_get(
        "/discover/movie",
        {
            "with_genres": genre_id,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "page": 1,
        },
    )

    cards = await tmdb_cards_from_results(
        data.get("results", []),
        limit,
    )

    return [
        card
        for card in cards
        if card.tmdb_id != tmdb_id
    ]


# -------------------------------------------------------------------------
# Search Bundle Service
# -------------------------------------------------------------------------
# Retrieves all information required for the movie details page:
#
#   1. Finds the best matching movie from TMDB.
#   2. Fetches complete movie details.
#   3. Generates content-based (TF-IDF) recommendations
#      from the local dataset.
#   4. Fetches genre-based recommendations from TMDB.
#
# This service is consumed by the /movie/search endpoint.
# -------------------------------------------------------------------------
async def get_movie_search_bundle(
    query: str = Query(..., min_length=1),
    tfidf_top_n: int = Query(12, ge=1, le=30),
    genre_limit: int = Query(12, ge=1, le=30),
):
    """
    Build the complete response required for the movie details screen.

    Parameters
    ----------
    query:
        Movie title entered by the user.

    tfidf_top_n:
        Number of content-based recommendations to return.

    genre_limit:
        Number of genre-based recommendations to return.

    Returns
    -------
    SearchBundleResponse
        Contains:
        - Selected movie details
        - TF-IDF recommendations
        - Genre recommendations
    """

    # ------------------------------------------------------------------
    # Step 1: Find the best matching movie on TMDB.
    # ------------------------------------------------------------------
    best = await tmdb_search_first(query)

    if not best:
        raise HTTPException(
            status_code=404,
            detail=f"No TMDB movie found for query: {query}",
        )

    # ------------------------------------------------------------------
    # Step 2: Retrieve complete movie information.
    # ------------------------------------------------------------------
    tmdb_id = int(best["id"])
    details = await get_movie_details(tmdb_id)

    # ------------------------------------------------------------------
    # Step 3: Generate TF-IDF recommendations.
    #
    # Prefer the official TMDB title since it usually matches the local
    # dataset better. If that fails, fall back to the user's original
    # search query.
    # ------------------------------------------------------------------
    tfidf_items: List[TFIDFRecommendation] = []

    try:
        recommendations = tfidf_recommend_titles(
            details.title,
            top_n=tfidf_top_n,
        )
    except Exception:
        try:
            recommendations = tfidf_recommend_titles(
                query,
                top_n=tfidf_top_n,
            )
        except Exception:
            recommendations = []

    # Attach TMDB poster and metadata for every recommendation.
    for title, score in recommendations:
        card = await attach_tmdb_card_by_title(title)

        tfidf_items.append(
            TFIDFRecommendation(
                title=title,
                score=score,
                tmdb=card,
            )
        )

    # ------------------------------------------------------------------
    # Step 4: Retrieve genre-based recommendations.
    #
    # This section is intentionally fault tolerant. Even if TMDB's
    # discover endpoint fails, the movie details and TF-IDF
    # recommendations are still returned.
    # ------------------------------------------------------------------
    try:
        genre_recs = await get_genre_recommendations(
            tmdb_id=details.tmdb_id,
            limit=genre_limit,
        )
    except Exception:
        genre_recs = []

    # ------------------------------------------------------------------
    # Step 5: Build the final API response.
    # ------------------------------------------------------------------
    return SearchBundleResponse(
        query=query,
        movie_details=details,
        tfidf_recommendations=tfidf_items,
        genre_recommendations=genre_recs,
    )