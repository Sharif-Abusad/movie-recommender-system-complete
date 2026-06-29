"""
Application Configuration

Loads:
- Environment variables
- API settings
- CORS settings
- Project paths
- Dataset paths
- External service configuration (TMDB)
"""

import os
from dotenv import load_dotenv

# =============================================================================
# Load Environment Variables
# =============================================================================

load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# =============================================================================
# CORS Configuration
# =============================================================================

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501",
).split(",")

# =============================================================================
# Project Paths
# =============================================================================

# app/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# app/data/
DATA_DIR = os.path.join(BASE_DIR, "data")

# =============================================================================
# Dataset Files
# =============================================================================

DF_PATH = os.path.join(DATA_DIR, "df.pkl")
INDICES_PATH = os.path.join(DATA_DIR, "indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(DATA_DIR, "tfidf_matrix.pkl")
TFIDF_PATH = os.path.join(DATA_DIR, "tfidf.pkl")

# =============================================================================
# TMDB Configuration
# =============================================================================

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise RuntimeError(
        "TMDB_API_KEY not found. Please add it to your .env file."
    )

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"