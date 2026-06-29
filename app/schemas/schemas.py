"""
Pydantic Schemas

Defines request and response models used throughout the Movie
Recommendation API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# TMDB Schemas
# =============================================================================

class TMDBMovieCard(BaseModel):
    """
    Lightweight movie information used in recommendation lists.
    """

    tmdb_id: int = Field(..., description="TMDB movie ID")
    title: str = Field(..., description="Movie title")
    poster_url: Optional[str] = Field(
        default=None,
        description="Poster image URL",
    )
    release_date: Optional[str] = Field(
        default=None,
        description="Movie release date",
    )
    vote_average: Optional[float] = Field(
        default=None,
        description="TMDB average rating",
    )


class TMDBMovieDetails(BaseModel):
    """
    Complete movie details returned by TMDB.
    """

    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None

    genres: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Movie genres",
    )


# =============================================================================
# Recommendation Schemas
# =============================================================================

class TFIDFRecommendation(BaseModel):
    """
    A single TF-IDF recommendation.
    """

    title: str
    score: float
    tmdb: Optional[TMDBMovieCard] = None


class SearchBundleResponse(BaseModel):
    """
    Response returned by /movie/search.
    """

    query: str

    movie_details: TMDBMovieDetails

    tfidf_recommendations: List[TFIDFRecommendation] = Field(
        default_factory=list
    )

    genre_recommendations: List[TMDBMovieCard] = Field(
        default_factory=list
    )