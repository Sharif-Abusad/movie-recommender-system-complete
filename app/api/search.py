"""
TMDB Search Routes

Provides movie search functionality using TMDB.

Used by:
- Search bar autocomplete
- Movie suggestion dropdowns
- Search results pages
"""

from fastapi import APIRouter, Query

from app.services.tmdb_services import tmdb_search_movies


router = APIRouter(
    prefix="",
    tags=["Search"],
)


# =============================================================================
# TMDB Movie Search
# =============================================================================

@router.get(
    "/tmdb/search",
    summary="Search movies from TMDB",
    description="""
Search TMDB movies by title.

Returns the raw TMDB response including:
- results
- page
- total_pages
- total_results

Useful for:
- Autocomplete suggestions
- Search result grids
- Movie discovery
""",
)
async def tmdb_search(
    query: str = Query(
        ...,
        min_length=1,
        description="Movie title or search keyword",
    ),
    page: int = Query(
        1,
        ge=1,
        le=10,
        description="TMDB result page number",
    ),
):
    """
    Search movies from TMDB.

    Args:
        query: Movie title or keyword.
        page: TMDB page number.

    Returns:
        Raw TMDB search response.
    """
    return await tmdb_search_movies(
        query=query,
        page=page,
    )