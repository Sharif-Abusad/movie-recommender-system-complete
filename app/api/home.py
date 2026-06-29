"""
Home API routes.

This module exposes endpoints for the application's home page,
such as Trending, Popular, Top Rated, Upcoming, and Now Playing movies.
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query

from app.schemas.schemas import TMDBMovieCard
from app.services.tmdb_services import (
    tmdb_cards_from_results,
    tmdb_get,
)

router = APIRouter(
    prefix="",
    tags=["Home"],
)


@router.get(
    "/home",
    response_model=List[TMDBMovieCard],
    summary="Get movies for the home page",
    description="""
Returns a list of movies for the selected category.

Supported categories:
- trending
- popular
- top_rated
- upcoming
- now_playing
""",
)
async def home(
    category: str = Query(
        default="popular",
        description="Movie category"
    ),
    limit: int = Query(
        default=24,
        ge=1,
        le=50,
        description="Maximum number of movies to return"
    ),
):
    """
    Fetch movies for the application's home screen.

    Parameters
    ----------
    category : str
        Movie category to fetch.

    limit : int
        Maximum number of movies returned.

    Returns
    -------
    List[TMDBMovieCard]
        List of movie cards suitable for display.
    """

    try:

        # Trending endpoint is different from the standard movie endpoints.
        if category == "trending":
            response = await tmdb_get(
                "/trending/movie/day",
                {"language": "en-US"},
            )

        else:
            allowed_categories = {
                "popular",
                "top_rated",
                "upcoming",
                "now_playing",
            }

            if category not in allowed_categories:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid movie category.",
                )

            response = await tmdb_get(
                f"/movie/{category}",
                {
                    "language": "en-US",
                    "page": 1,
                },
            )

        return await tmdb_cards_from_results(
            response.get("results", []),
            limit=limit,
        )

    # Re-raise FastAPI exceptions unchanged.
    except HTTPException:
        raise

    # Catch unexpected server-side errors.
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load home movies: {str(exc)}",
        )