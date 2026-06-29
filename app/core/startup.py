"""
Application Lifespan

Responsible for:
- Initializing shared application resources.
- Loading ML artifacts.
- Creating reusable HTTP clients.
- Cleaning up resources during shutdown.
"""

from contextlib import asynccontextmanager
import pickle

import httpx
from fastapi import FastAPI

from app.core.config import (
    DF_PATH,
    INDICES_PATH,
    TFIDF_MATRIX_PATH,
    TFIDF_PATH,
)
from app.core.state import state
from app.services.tfidf_services import build_title_to_index_map


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize application resources during startup
    and release them during shutdown.
    """

    print("=" * 70)
    print("Starting Movie Recommendation API...")
    print("=" * 70)

    # =========================================================================
    # Create reusable HTTP client
    # =========================================================================

    state.client = httpx.AsyncClient(
        timeout=httpx.Timeout(20.0),
        limits=httpx.Limits(
            max_connections=50,
            max_keepalive_connections=20,
        ),
    )

    # =========================================================================
    # Load ML artifacts
    # =========================================================================

    print("Loading movie dataset...")
    with open(DF_PATH, "rb") as f:
        state.df = pickle.load(f)

    print("Loading title indices...")
    with open(INDICES_PATH, "rb") as f:
        state.indices_obj = pickle.load(f)

    print("Loading TF-IDF matrix...")
    with open(TFIDF_MATRIX_PATH, "rb") as f:
        state.tfidf_matrix = pickle.load(f)

    print("Loading TF-IDF vectorizer...")
    with open(TFIDF_PATH, "rb") as f:
        state.tfidf_obj = pickle.load(f)

    # =========================================================================
    # Build lookup cache
    # =========================================================================

    print("Building title lookup cache...")
    state.title_to_idx = build_title_to_index_map(state.indices_obj)

    # =========================================================================
    # Validate loaded resources
    # =========================================================================

    if state.df is None or "title" not in state.df.columns:
        raise RuntimeError(
            "Invalid dataset. df.pkl must contain a DataFrame with a 'title' column."
        )

    if not state.is_initialized:
        raise RuntimeError(
            "Application state failed to initialize."
        )

    print("Application started successfully.")

    # Application runs here
    yield

    # =========================================================================
    # Shutdown
    # =========================================================================

    print("Shutting down Movie Recommendation API...")

    if state.http_client:
        await state.http_client.aclose()

    print("Shutdown complete.")