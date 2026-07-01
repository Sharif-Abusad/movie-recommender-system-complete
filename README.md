# 🎬 Movie Recommendation System

A full-stack **Movie Recommendation System** built with **FastAPI** and **Streamlit** that combines **content-based filtering (TF-IDF)** with **The Movie Database (TMDB) API** to deliver intelligent and visually rich movie recommendations.

The application provides real-time movie search, detailed movie information, personalized recommendations, and an interactive user interface.

---

## 🚀 Live Demo

**Frontend:** *https://movie-recommender-system-complete.streamlit.app*

**Backend API:** *https://movie-recommender-system-3n2v.onrender.com*

**API Documentation:**

```
https:///movie-recommender-system-3n2v.onrender.com/docs
```

---

# Features

### 🎥 Movie Search

* Search movies using the TMDB API
* Autocomplete search suggestions
* High-quality movie posters
* Release dates and ratings

### 📄 Movie Details

* Movie overview
* Poster and backdrop
* Genres
* Release information
* TMDB ratings

### 🤖 Content-Based Recommendations

* TF-IDF based recommendation engine
* Recommends movies with similar plot descriptions
* Local recommendation model for fast inference

### 🎭 Genre-Based Recommendations

* Discovers popular movies from the selected movie's primary genre
* Powered by TMDB Discover API

### ⚡ FastAPI Backend

* Modular production-ready architecture
* Async API endpoints
* Shared HTTP client
* Retry mechanism with exponential backoff
* Automatic OpenAPI documentation

### 🎨 Streamlit Frontend

* Responsive UI
* Movie cards
* Interactive recommendation panels
* Clean user experience

---

# Tech Stack

## Backend

* FastAPI
* Uvicorn
* HTTPX
* Pydantic
* NumPy
* Pandas
* Scikit-learn

## Frontend

* Streamlit
* Requests

## APIs

* TMDB API

---

# Project Structure

```text
movie-recommendation/
│
├── app/
│   ├── api/
│   │   ├── home.py
│   │   ├── movie.py
│   │   ├── recommend.py
│   │   └── search.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── startup.py
│   │   └── state.py
│   │
│   ├── schemas/
│   │   └── schemas.py
│   │
│   ├── services/
│   │   ├── tmdb_services.py
│   │   └── tfidf_services.py
│   │
│   └── main.py
│
├── app.py
│
├── data/
│   ├── df.pkl
│   ├── indices.pkl
│   ├── tfidf.pkl
│   └── tfidf_matrix.pkl
│
├── requirements.txt
├── README.md
└── .env.example
```

---

# Recommendation Pipeline

```text
User Search
      │
      ▼
 TMDB Search API
      │
      ▼
 Best Matching Movie
      │
      ├──────────────► Movie Details
      │
      ├──────────────► TF-IDF Recommendation Engine
      │                     │
      │                     ▼
      │           Similar Movies
      │
      └──────────────► Genre Discovery
                            │
                            ▼
                 Genre Recommendations
```

---

# Installation

## Clone the repository

```bash
git clone https://github.com/your-username/movie-recommendation-system.git

cd movie-recommendation-system
```

---

## Create a virtual environment

```bash
python -m venv venv
```

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file.

```env
TMDB_API_KEY=your_tmdb_api_key

API_HOST=0.0.0.0
API_PORT=8000

DEBUG=False

ALLOWED_ORIGINS=http://localhost:8501
```

---

# Run the Backend

```bash
uvicorn app.main:app --reload
```

Backend will be available at

```
http://localhost:8000
```

Swagger Documentation

```
http://localhost:8000/docs
```

---

# Run the Frontend

```bash
streamlit run frontend/app.py
```

---

# API Endpoints

| Method | Endpoint              | Description                    |
| ------ | --------------------- | ------------------------------ |
| GET    | `/home`               | Home page movie feed           |
| GET    | `/tmdb/search`        | Search movies                  |
| GET    | `/movie/id/{tmdb_id}` | Movie details                  |
| GET    | `/movie/search`       | Complete recommendation bundle |
| GET    | `/recommend/tfidf`    | TF-IDF recommendations         |
| GET    | `/recommend/genre`    | Genre recommendations          |
| GET    | `/health`             | Health check                   |

---

# Deployment

## Backend

* Render

Build Command

```bash
pip install -r requirements.txt
```

Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Frontend

* Streamlit Community Cloud

Configure the following secret:

```toml
API_BASE="https://your-render-backend.onrender.com"
TIMEOUT="60"
```

---

# Future Improvements

* Collaborative Filtering
* Hybrid Recommendation System
* User Authentication
* Watchlist
* Favorites
* Recommendation Caching
* Docker Support
* CI/CD Pipeline
* Unit & Integration Tests
* Logging & Monitoring

---

# Author

**Abu Sharif**

GitHub: https://github.com/sharif-abusad

LinkedIn: https://linkedin.com/in/abu-sharif

---

# License

This project is licensed under the MIT License.
