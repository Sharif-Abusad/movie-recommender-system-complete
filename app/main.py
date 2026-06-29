"""
Application entry point.

Responsibilities:
- Create FastAPI application
- Configure middleware
- Register API routers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.home import router as home_router
from app.api.movie import router as movie_router
from app.api.recommend import router as recommend_router
from app.api.search import router as search_router
from app.core.config import ALLOWED_ORIGINS
from app.core.startup import lifespan


# ==========================================================
# FastAPI Application
# ==========================================================

app = FastAPI(
    title="Movie Recommendation API",
    description="REST API for movie search and recommendations using TMDB and TF-IDF.",
    version="1.0.0",
    lifespan=lifespan,
)


# ==========================================================
# Middleware
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# Health & Root Endpoints
# ==========================================================

@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "Movie Recommendation API",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
async def health():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
    }


# ==========================================================
# API Routers
# ==========================================================

app.include_router(home_router)
app.include_router(search_router)
app.include_router(movie_router)
app.include_router(recommend_router)