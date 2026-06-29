"""
TF-IDF recommendation service.

Responsible for:
- Building the title → dataframe index mapping
- Looking up movies by title
- Computing TF-IDF similarity recommendations
"""

from typing import Any, Dict, List, Tuple

import numpy as np
from fastapi import HTTPException

from app.core.state import state


# ==========================================================
# Private Helpers
# ==========================================================

def _normalize_title(title: str) -> str:
    """
    Normalize movie titles for case-insensitive lookup.
    """
    return title.strip().lower()


def _ensure_resources_loaded() -> None:
    """
    Ensure TF-IDF resources have been loaded during application startup.
    """
    if (
        state.df is None
        or state.tfidf_matrix is None
        or state.tfidf_obj is None
        or state.title_to_idx is None
    ):
        raise HTTPException(
            status_code=500,
            detail="TF-IDF resources have not been initialized.",
        )


# ==========================================================
# Title Index Mapping
# ==========================================================

def build_title_to_index_map(indices: Any) -> Dict[str, int]:
    """
    Build a normalized title → dataframe index mapping.

    Supports:
    - dict
    - pandas Series
    """

    mapping: Dict[str, int] = {}

    try:
        for title, idx in indices.items():
            mapping[_normalize_title(title)] = int(idx)

    except AttributeError as exc:
        raise RuntimeError(
            "indices.pkl must be a dictionary or pandas Series."
        ) from exc

    return mapping


def get_local_index(title: str) -> int:
    """
    Return dataframe index for a movie title.
    """

    _ensure_resources_loaded()

    idx = state.title_to_idx.get(_normalize_title(title))

    if idx is None:
        raise HTTPException(
            status_code=404,
            detail=f"Movie '{title}' not found in local dataset.",
        )

    return idx


# ==========================================================
# Recommendation Engine
# ==========================================================

def tfidf_recommend_titles(
    query_title: str,
    top_n: int = 10,
) -> List[Tuple[str, float]]:
    """
    Generate TF-IDF recommendations.

    Returns:
        [
            ("Toy Story", 0.98),
            ("Jumanji", 0.94),
            ...
        ]
    """

    _ensure_resources_loaded()

    query_idx = get_local_index(query_title)

    query_vector = state.tfidf_matrix[query_idx]

    similarity_scores = (
        state.tfidf_matrix @ query_vector.T
    ).toarray().ravel()

    ranked_indices = np.argsort(-similarity_scores)

    recommendations: List[Tuple[str, float]] = []

    for movie_idx in ranked_indices:

        if movie_idx == query_idx:
            continue

        try:
            movie_title = str(state.df.iloc[movie_idx]["title"])
        except Exception:
            continue

        recommendations.append(
            (
                movie_title,
                float(similarity_scores[movie_idx]),
            )
        )

        if len(recommendations) >= top_n:
            break

    return recommendations