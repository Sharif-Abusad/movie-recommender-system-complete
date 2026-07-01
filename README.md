<div align="center">

<img src="https://readme-typing-svg.herokuapp.com?font=Playfair+Display&size=42&duration=3000&pause=1000&color=F5A623&center=true&vCenter=true&width=600&lines=🎬+CineMatch;Movie+Recommendation+System" alt="CineMatch" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-TF--IDF-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![TMDB](https://img.shields.io/badge/TMDB-API-01D277?style=for-the-badge&logo=themoviedatabase&logoColor=white)](https://www.themoviedb.org)
[![Render](https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

**A full-stack movie recommendation engine combining content-based TF-IDF filtering with the TMDB API — delivering intelligent, visually rich film discovery in real time.**

<br/>

[🚀 Live Demo](#-live-demo) · [📸 Screenshots](#-screenshots) · [🏗️ Architecture](#%EF%B8%8F-architecture) · [⚙️ Installation](#%EF%B8%8F-installation) · [📡 API Reference](#-api-reference) · [🤝 Contributing](#-contributing)

</div>

---

## 🚀 Live Demo

| Service | URL |
|---|---|
| 🎨 **Frontend** | [movie-recommender-system-complete.streamlit.app](https://movie-recommender-system-complete.streamlit.app) |
| ⚡ **Backend API** | [movie-recommender-system-3n2v.onrender.com](https://movie-recommender-system-3n2v.onrender.com) |
| 📖 **API Docs** | [/docs](https://movie-recommender-system-3n2v.onrender.com/docs) · [/redoc](https://movie-recommender-system-3n2v.onrender.com/redoc) |

> **Note:** The backend is hosted on Render's free tier and may take 30–60 seconds to wake up on first request.

---

## 📸 Screenshots

<details open>
<summary><b>🏠 Home — Browsable Movie Feed</b></summary>
<br/>
<p align="center">
  <img src="images/home.png" width="900" alt="Home Page"/>
</p>
</details>

<details>
<summary><b>🔍 Search — Real-time Movie Search</b></summary>
<br/>
<p align="center">
  <img src="images/search.png" width="900" alt="Search Page"/>
</p>
</details>

<details>
<summary><b>🤖 Content-Based Recommendations (TF-IDF)</b></summary>
<br/>
<p align="center">
  <img src="images/content_recommendations.png" width="900" alt="TF-IDF Recommendations"/>
</p>
</details>

<details>
<summary><b>🎭 Genre Recommendations</b></summary>
<br/>
<p align="center">
  <img src="images/genre_recommendations.png" width="900" alt="Genre Recommendations"/>
</p>
</details>

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| 🔍 | **Smart Search** | Real-time movie search powered by TMDB with instant results |
| 🤖 | **Content-Based Filtering** | TF-IDF cosine similarity on movie plots and metadata |
| 🎭 | **Genre Discovery** | Discover top-rated films within the same genre via TMDB |
| 🎬 | **Rich Movie Details** | Posters, backdrops, ratings, genres, overview, and release info |
| ⚡ | **Async FastAPI Backend** | High-performance REST API with full OpenAPI documentation |
| 🎨 | **Cinematic UI** | Dark-themed Streamlit frontend with hero banners and card grids |
| 🔄 | **Parallel Fetching** | Concurrent TMDB poster resolution for fast recommendation rendering |
| 📦 | **Cached Responses** | `st.cache_data` on all API calls for snappy repeat queries |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER BROWSER                         │
└─────────────────────┬───────────────────────────────────┘
                      │  HTTP
                      ▼
┌─────────────────────────────────────────────────────────┐
│              STREAMLIT FRONTEND  (app.py)               │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐    │
│  │  Home    │  │  Search  │  │  Details / Recs    │    │
│  └──────────┘  └──────────┘  └────────────────────┘    │
│                                                         │
│  ThreadPoolExecutor — parallel API calls                │
└────────────────────────┬────────────────────────────────┘
                         │  REST (JSON)
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND  (app/main.py)             │
│                                                         │
│  ┌──────────────────┐    ┌──────────────────────────┐   │
│  │   TMDB Service   │    │     TF-IDF Engine        │   │
│  │  (httpx async)   │    │  (scikit-learn + numpy)  │   │
│  └────────┬─────────┘    └──────────┬───────────────┘   │
│           │                         │                   │
│           ▼                         ▼                   │
│  ┌──────────────┐         ┌──────────────────────┐      │
│  │  TMDB API    │         │  Pickle Data Store   │      │
│  │  (external)  │         │  df · indices ·      │      │
│  └──────────────┘         │  tfidf · matrix      │      │
│                           └──────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### Recommendation Pipeline

```
User Query
    │
    ├──► TMDB Search  ──► Best Match  ──► Movie Details
    │                                          │
    ├──► TF-IDF Engine                         ▼
    │       │                         Poster + Backdrop
    │       ▼                         Genres, Overview
    │   Cosine Similarity
    │       │
    │       ▼
    │   Top-N Similar Titles
    │       │
    │       ▼
    │   Parallel TMDB Poster Fetch (ThreadPoolExecutor)
    │
    └──► Genre Discovery  ──► TMDB /discover/movie  ──► Genre Grid
```

---

## 🗂️ Project Structure

```
movie-recommendation/
│
├── app/                          # FastAPI backend
│   ├── api/
│   │   ├── home.py               # /home endpoint — trending/popular feeds
│   │   ├── movie.py              # /movie/id and /movie/search endpoints
│   │   ├── recommend.py          # /recommend/tfidf and /recommend/genre
│   │   └── search.py             # /tmdb/search endpoint
│   │
│   ├── core/
│   │   ├── config.py             # Environment config (pydantic-settings)
│   │   ├── startup.py            # Pickle loading on startup
│   │   └── state.py              # Global in-memory state (df, matrix, etc.)
|   |
|   ├── data/                         # Pre-computed ML artifacts (not in git)
│   |   ├── df.pkl                    # Processed movie DataFrame
│   |   ├── indices.pkl               # Title → matrix index mapping
│   |   ├── tfidf.pkl                 # Fitted TfidfVectorizer
│   |   └── tfidf_matrix.pkl          # Sparse TF-IDF feature matrix
|   | 
│   ├── schemas/
│   │   └── schemas.py            # Pydantic request/response models
│   │
│   ├── services/
│   │   ├── tmdb_services.py      # Async TMDB API client (httpx + retry)
│   │   └── tfidf_services.py     # TF-IDF cosine similarity logic
│   │
│   └── main.py                   # FastAPI app, CORS, router registration
│
├── images/                       # Application screenshots
│   ├── cotent_recommendations.png
│   ├── genre_recommendations.png               
│   ├── home.png                 
│   └── search.png  
|
├── notebooks/                    # Data preparation and model training
|   ├── movies.ipynb 
|   └── movies_metadata.csv   
|
├── app.py                        # Streamlit UI
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.11+
- A free [TMDB API key](https://www.themoviedb.org/settings/api)
- The four `.pkl` data files (see [Data Setup](#data-setup))

### 1. Clone the repository

```bash
git clone https://github.com/sharif-abusad/movie-recommendation-system.git
cd movie-recommendation-system
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
TMDB_API_KEY=your_tmdb_api_key_here

API_HOST=0.0.0.0
API_PORT=8000

DEBUG=False

ALLOWED_ORIGINS=http://localhost:8501
```

### 5. Data Setup

Place the pre-computed pickle files in the `data/` directory:

```
data/
├── df.pkl
├── indices.pkl
├── tfidf.pkl
└── tfidf_matrix.pkl
```

> To regenerate these files from scratch, run the notebook in `notebooks/`.

---

## 🖥️ Running Locally

### Start the backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Resource | URL |
|---|---|
| API Base | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

### Start the frontend

```bash
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501`.

---

## 📡 API Reference

### Base URL

```
http://localhost:8000
```

### Endpoints

| Method | Endpoint | Description | Key Parameters |
|---|---|---|---|
| `GET` | `/health` | Health check | — |
| `GET` | `/home` | Trending / popular / top-rated feed | `category`, `limit` |
| `GET` | `/tmdb/search` | Full-text TMDB movie search | `query`, `page` |
| `GET` | `/movie/id/{tmdb_id}` | Movie details by TMDB ID | `tmdb_id` |
| `GET` | `/movie/search` | Complete bundle: details + TF-IDF + genre recs | `query`, `tfidf_top_n`, `genre_limit` |
| `GET` | `/recommend/tfidf` | TF-IDF recommendations (titles + scores only) | `title`, `top_n` |
| `GET` | `/recommend/genre` | Genre-based discovery via TMDB | `tmdb_id`, `limit` |

### Example Requests

```bash
# Get trending movies
curl "http://localhost:8000/home?category=trending&limit=12"

# Search for a movie
curl "http://localhost:8000/tmdb/search?query=inception"

# TF-IDF recommendations
curl "http://localhost:8000/recommend/tfidf?title=Inception&top_n=10"

# Full recommendation bundle
curl "http://localhost:8000/movie/search?query=The+Dark+Knight&tfidf_top_n=12&genre_limit=12"
```

<details>
<summary><b>Example Response — <code>GET /recommend/tfidf</code></b></summary>

```json
[
  { "title": "Batman Begins", "score": 0.612 },
  { "title": "The Dark Knight Rises", "score": 0.589 },
  { "title": "Watchmen", "score": 0.431 }
]
```

</details>

<details>
<summary><b>Example Response — <code>GET /movie/id/{tmdb_id}</code></b></summary>

```json
{
  "tmdb_id": 155,
  "title": "The Dark Knight",
  "overview": "Batman raises the stakes in his war on crime...",
  "release_date": "2008-07-18",
  "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
  "backdrop_url": "https://image.tmdb.org/t/p/w1280/hkBaDkMWbLaf8B1lsWsKX7Ew3Xq.jpg",
  "genres": [
    { "id": 28, "name": "Action" },
    { "id": 80, "name": "Crime" },
    { "id": 18, "name": "Drama" }
  ]
}
```

</details>

---

## 🚢 Deployment

### Backend — Render

1. Push your repo to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Set the following:

| Setting | Value |
|---|---|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Environment Variables** | `TMDB_API_KEY`, `DEBUG=False` |

### Frontend — Streamlit Community Cloud

1. Connect your GitHub repo at [share.streamlit.io](https://share.streamlit.io)
2. Set **Main file path** to `frontend/app.py`
3. Add secrets under **Settings → Secrets**:

```toml
API_BASE = "https://your-render-backend.onrender.com"
TIMEOUT  = "60"
```

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com)** — async REST API framework
- **[Uvicorn](https://www.uvicorn.org)** — ASGI server
- **[HTTPX](https://www.python-httpx.org)** — async HTTP client for TMDB calls
- **[Pydantic](https://docs.pydantic.dev)** — data validation and serialisation
- **[Scikit-learn](https://scikit-learn.org)** — TF-IDF vectoriser
- **[NumPy](https://numpy.org)** — cosine similarity computation
- **[Pandas](https://pandas.pydata.org)** — movie DataFrame

### Frontend
- **[Streamlit](https://streamlit.io)** — interactive UI framework
- **[Requests](https://docs.python-requests.org)** — REST API client
- **[concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)** — parallel poster fetching

### External APIs
- **[TMDB API](https://developer.themoviedb.org/docs)** — movie data, posters, and genre discovery

---

## 🗺️ Roadmap

- [ ] Collaborative filtering (user-based / item-based)
- [ ] Hybrid recommendation (TF-IDF + collaborative)
- [ ] User authentication and profiles
- [ ] Watchlist and favourites
- [ ] Server-side recommendation caching (Redis)
- [ ] Docker + docker-compose setup
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Unit and integration tests (pytest)
- [ ] Structured logging and monitoring (Sentry / Grafana)
- [ ] Mobile-responsive PWA

---

## 🤝 Contributing

Contributions are welcome and appreciated.

```bash
# 1. Fork the repository
# 2. Create a feature branch
git checkout -b feature/your-feature-name

# 3. Commit your changes
git commit -m "feat: add your feature"

# 4. Push and open a Pull Request
git push origin feature/your-feature-name
```

Please follow [Conventional Commits](https://www.conventionalcommits.org) for commit messages and open an issue before starting large changes.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

<div align="center">

**Abu Sharif**

[![GitHub](https://img.shields.io/badge/GitHub-sharif--abusad-181717?style=for-the-badge&logo=github)](https://github.com/sharif-abusad)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-abu--sharif-0A66C2?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/abu-sharif)

*If you found this project useful, consider giving it a ⭐ on GitHub — it helps a lot!*

</div>

---

<div align="center">
<sub>Built with ❤️ using FastAPI, Streamlit, and the TMDB API</sub>
</div>