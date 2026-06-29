"""
Application Global State

This module stores shared application resources that are initialized
during the FastAPI lifespan startup and reused across incoming requests.

These objects are loaded once to avoid repeatedly loading large
pickle files from disk.
"""

from typing import Any, Dict, Optional

import pandas as pd
import httpx

class AppState:
    """
    Shared application state.

    Attributes
    ----------
    df : pd.DataFrame | None
        Main movie dataset.

    indices_obj : Any
        Original title-to-index mapping loaded from `indices.pkl`.

    tfidf_matrix : Any
        Sparse TF-IDF feature matrix used for similarity computation.

    tfidf_obj : Any
        Trained TF-IDF Vectorizer.

    title_to_idx : dict[str, int] | None
        Normalized movie title -> dataframe index lookup table.
    """

    def __init__(self) -> None:
        # =====================================================================
        # Dataset Resources
        # =====================================================================
        self.df: Optional[pd.DataFrame] = None
        # HTTP client
        self.client: Optional[httpx.AsyncClient] = None

        self.indices_obj: Any = None
        self.tfidf_matrix: Any = None
        self.tfidf_obj: Any = None

        # =====================================================================
        # Cached Lookup Tables
        # =====================================================================
        self.title_to_idx: Optional[Dict[str, int]] = None

    @property
    def is_initialized(self) -> bool:
        """
        Returns True when all required resources have been loaded.
        """
        return (
            self.df is not None
            and self.indices_obj is not None
            and self.tfidf_matrix is not None
            and self.tfidf_obj is not None
            and self.title_to_idx is not None
        )


# =============================================================================
# Singleton Application State
# =============================================================================

state = AppState()