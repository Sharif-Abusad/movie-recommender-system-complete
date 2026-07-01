import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from app.core.config import TMDB_IMAGE_BASE_URL
load_dotenv()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
# Generous timeout — bundle endpoint makes ~12 sequential TMDB calls

API_BASE = os.getenv("API_BASE")
TIMEOUT = int(os.getenv("TIMEOUT", 60))

st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [data-testid="stApp"] {
    background: #0A0A0F !important;
    color: #E8E8F0 !important;
    font-family: 'Inter', sans-serif;
}
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D0D18 !important;
    border-right: 1px solid #1E1E2E !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
.nav-brand { padding: 28px 20px 24px; border-bottom: 1px solid #1E1E2E; margin-bottom: 12px; }
.nav-brand h1 {
    font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 900;
    background: linear-gradient(135deg, #F5A623, #FF6B35);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; letter-spacing: -0.5px;
}
.nav-brand p { color: #6B6B8A; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important; align-items: center !important; gap: 10px !important;
    padding: 10px 20px !important; border-radius: 8px !important; cursor: pointer !important;
    font-size: 14px !important; font-weight: 500 !important; color: #9090B0 !important;
    transition: all 0.15s ease !important; background: transparent !important;
    border: none !important; margin: 1px 8px !important; width: calc(100% - 16px) !important;
}
[data-testid="stSidebar"] .stRadio > div > label:hover { background: #1E1E2E !important; color: #E8E8F0 !important; }
[data-testid="stSidebar"] .stRadio [aria-checked="true"] {
    background: linear-gradient(135deg, rgba(245,166,35,0.15), rgba(255,107,53,0.08)) !important;
    color: #F5A623 !important; border-left: 2px solid #F5A623 !important; padding-left: 18px !important;
}
section[data-testid="stMain"] .block-container { padding: 32px 40px !important; max-width: 1400px !important; }

/* ── Hero ── */
.cm-hero-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(90deg, rgba(10,10,15,0.97) 0%, rgba(10,10,15,0.82) 42%, rgba(10,10,15,0.25) 70%, transparent 100%);
    display: flex; align-items: flex-end; padding: 36px;
}
.cm-genre-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.cm-pill {
    background: rgba(245,166,35,0.15); border: 1px solid rgba(245,166,35,0.4);
    color: #F5A623; font-size: 10px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.8px;
}
.cm-hero-title {
    font-family: 'Playfair Display', serif; font-size: 38px; font-weight: 900;
    color: #FFFFFF; line-height: 1.1; margin-bottom: 10px; letter-spacing: -1px;
}
.cm-hero-overview {
    font-size: 13px; color: #B0B0C8; line-height: 1.6; margin-bottom: 16px;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.cm-hero-stats { display: flex; align-items: center; gap: 24px; }
.cm-stat-label { font-size: 10px; color: #6B6B8A; letter-spacing: 1px; text-transform: uppercase; }
.cm-stat-val   { font-size: 18px; font-weight: 700; color: #F5A623; line-height: 1.3; }

/* ── st.image inside hero: fill the container ── */
.cm-hero [data-testid="stImage"] { line-height: 0 !important; }
.cm-hero [data-testid="stImage"] img {
    width: 100% !important; display: block !important;
    object-fit: cover !important; border-radius: 0 !important;
}

/* ── Movie cards ── */
.cm-card {
    background: #141420; border-radius: 12px; overflow: hidden;
    border: 1px solid #1E1E2E;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    margin-bottom: 4px;
}
.cm-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(245,166,35,0.15);
    border-color: rgba(245,166,35,0.35);
}
/* Poster image: fixed 2:3 ratio, no overflow */
.cm-card [data-testid="stImage"] { line-height: 0 !important; overflow: hidden; }
.cm-card [data-testid="stImage"] img {
    width: 100% !important; aspect-ratio: 2/3 !important;
    object-fit: cover !important; display: block !important;
    border-radius: 12px 12px 0 0 !important;
    margin: 0 !important; padding: 0 !important;
}
/* Card body text — clamp, no overflow */
.cm-card-body { padding: 10px 12px 10px; }
.cm-card-title {
    font-size: 12px; font-weight: 600; color: #E8E8F0; line-height: 1.35; margin-bottom: 5px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cm-card-meta { display: flex; align-items: center; justify-content: space-between; gap: 4px; flex-wrap: nowrap; }
.cm-card-year   { font-size: 11px; color: #6B6B8A; flex-shrink: 0; }
.cm-card-rating { font-size: 11px; font-weight: 600; color: #F5A623; flex-shrink: 0; }
.cm-score {
    display: inline-block;
    background: rgba(245,166,35,0.15); border: 1px solid rgba(245,166,35,0.3);
    color: #F5A623; font-size: 10px; font-weight: 700;
    padding: 1px 5px; border-radius: 20px; flex-shrink: 0;
}

/* ── Details button ── */
.stButton > button {
    background: linear-gradient(135deg, #F5A623, #FF6B35) !important;
    color: #0A0A0F !important; border: none !important;
    border-radius: 0 0 10px 10px !important;
    font-weight: 700 !important; font-size: 12px !important;
    padding: 8px 0 !important; width: 100% !important;
    transition: opacity 0.2s !important; font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Section header ── */
.cm-section { display: flex; align-items: center; gap: 16px; margin: 36px 0 18px; }
.cm-section h2 { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #E8E8F0; white-space: nowrap; }
.cm-section-div { flex: 1; height: 1px; background: linear-gradient(90deg, #2A2A40, transparent); }
.cm-section-lbl { font-size: 10px; color: #6B6B8A; letter-spacing: 1.2px; text-transform: uppercase; white-space: nowrap; }

/* ── Page title ── */
.cm-page-title { font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 900; color: #FFF; margin-bottom: 4px; letter-spacing: -0.5px; }
.cm-page-sub   { font-size: 13px; color: #6B6B8A; margin-bottom: 28px; }

/* ── Detail page ── */
.cm-detail-title { font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 900; color: #FFF; line-height: 1.1; margin-bottom: 10px; letter-spacing: -0.8px; }
.cm-detail-overview { font-size: 14px; color: #B0B0C8; line-height: 1.7; margin-bottom: 22px; }
.cm-stat-card { background: #141420; border: 1px solid #1E1E2E; border-radius: 10px; padding: 14px 18px; text-align: center; }
.cm-stat-card-val   { font-size: 22px; font-weight: 700; color: #F5A623; }
.cm-stat-card-label { font-size: 10px; color: #6B6B8A; text-transform: uppercase; letter-spacing: 1px; margin-top: 3px; }

/* ── Empty state ── */
.cm-empty { text-align: center; padding: 70px 40px; color: #4A4A6A; }
.cm-empty .ei { font-size: 44px; margin-bottom: 14px; }
.cm-empty h3  { font-size: 17px; color: #6B6B8A; margin-bottom: 6px; }
.cm-empty p   { font-size: 13px; }

/* ── Input ── */
[data-testid="stTextInput"] > div > div > input {
    background: #141420 !important; border: 1px solid #2A2A40 !important;
    border-radius: 10px !important; color: #E8E8F0 !important;
    padding: 14px 18px !important; font-size: 15px !important; font-family: 'Inter', sans-serif !important;
}
[data-testid="stTextInput"] > div > div > input:focus { border-color: #F5A623 !important; box-shadow: 0 0 0 3px rgba(245,166,35,0.1) !important; }
[data-testid="stTextInput"] > div > div > input::placeholder { color: #4A4A6A !important; }
[data-testid="stSelectbox"] > div > div { background: #141420 !important; border: 1px solid #2A2A40 !important; border-radius: 10px !important; color: #E8E8F0 !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid #1E1E2E !important; background: transparent !important; }
[data-testid="stTabs"] [role="tab"] { color: #6B6B8A !important; font-size: 13px !important; font-weight: 500 !important; padding: 10px 20px !important; border: none !important; background: transparent !important; border-bottom: 2px solid transparent !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #F5A623 !important; border-bottom-color: #F5A623 !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0A0A0F; }
::-webkit-scrollbar-thumb { background: #2A2A40; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #F5A623; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# API HELPERS  (all with generous TIMEOUT)
# ─────────────────────────────────────────────
def api_get(path: str, params: Dict = None, silent: bool = False) -> Optional[Any]:
    try:
        r = requests.get(f"{API_BASE}{path}", params=params or {}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        if not silent:
            st.error("⚠️ Cannot reach the backend. Make sure FastAPI is running on localhost:8000.")
        return None
    except requests.exceptions.Timeout:
        if not silent:
            st.warning("⏱️ The request timed out. The backend is still computing — try again in a moment.")
        return None
    except requests.exceptions.HTTPError as e:
        if not silent:
            st.error(f"API error {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        if not silent:
            st.error(f"Unexpected error: {e}")
        return None


@st.cache_data(ttl=300)
def get_home_feed(category: str, limit: int = 24):
    return api_get("/home", {"category": category, "limit": limit})

@st.cache_data(ttl=60)
def search_movies(query: str, page: int = 1):
    return api_get("/tmdb/search", {"query": query, "page": page})

@st.cache_data(ttl=300)
def get_movie_details(tmdb_id: int):
    return api_get(f"/movie/id/{tmdb_id}")

@st.cache_data(ttl=300)
def get_tfidf_recs(query: str, top_n: int = 12):
    """Calls the lightweight /recommend/tfidf endpoint — no TMDB poster fetching."""
    return api_get("/recommend/tfidf", {"title": query, "top_n": top_n})

@st.cache_data(ttl=300)
def get_genre_recs(tmdb_id: int, limit: int = 12):
    return api_get("/recommend/genre", {"tmdb_id": tmdb_id, "limit": limit})

@st.cache_data(ttl=120)
def tmdb_search_first(query: str) -> Optional[dict]:
    """Returns the first TMDB result for a query string."""
    raw = api_get("/tmdb/search", {"query": query, "page": 1})
    if raw and raw.get("results"):
        return raw["results"][0]
    return None

def fetch_poster_for_title(title: str) -> Optional[str]:
    """Quick TMDB search to get a poster URL for a local title."""
    m = tmdb_search_first(title)
    if m and m.get("poster_path"):
        return f"TMDB_IMAGE_BASE_URL{m['poster_path']}"
    return None

def health_check() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────
# NORMALISE — handle TMDBMovieCard and TFIDFRecItem
# ─────────────────────────────────────────────
def normalise(movie: dict) -> dict:
    if "tmdb" in movie and isinstance(movie["tmdb"], dict):
        t = movie["tmdb"]
        return {
            "title":        movie.get("title") or t.get("title", "Unknown"),
            "poster_url":   t.get("poster_url"),
            "release_date": t.get("release_date"),
            "vote_average": t.get("vote_average"),
            "tmdb_id":      t.get("tmdb_id"),
            "score":        movie.get("score"),
        }
    return {
        "title":        movie.get("title", "Unknown"),
        "poster_url":   movie.get("poster_url"),
        "release_date": movie.get("release_date"),
        "vote_average": movie.get("vote_average"),
        "tmdb_id":      movie.get("tmdb_id"),
        "score":        movie.get("score"),
    }

def safe_text(s: str) -> str:
    """Escape any stray HTML in user-facing strings."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ─────────────────────────────────────────────
# COMPONENT: Hero banner
# Uses st.image for the backdrop (Streamlit owns the <img>).
# The overlay is a single self-contained HTML block with NO nested
# markdown calls that could leave orphaned tags.
# ─────────────────────────────────────────────
def render_hero(backdrop_url: str, title: str, overview: str,
                genres: list, year: str, rating: float = None, height: int = 400):
    pills = "".join(
        f'<span class="cm-pill">{safe_text(g["name"])}</span>'
        for g in (genres or [])[:4]
    )
    overview_safe = safe_text(overview)[:380]
    year_safe     = safe_text(year) or "—"
    title_safe    = safe_text(title)

    rating_html = (
        f'<span style="margin-left:20px;">'
        f'<div class="cm-stat-label">Rating</div>'
        f'<div class="cm-stat-val">★ {rating:.1f}</div>'
        f'</span>'
    ) if rating else ""

    # Wrapper sets the height; st.image fills it via CSS
    st.markdown(f'<div class="cm-hero" style="height:{height}px; overflow:hidden;">',
                unsafe_allow_html=True)
    st.image(backdrop_url, width=None)

    # Overlay: one atomic, fully-closed HTML block
    st.markdown(
        f'<div class="cm-hero-overlay">'
        f'<div class="cm-hero-inner">'
        f'<div class="cm-genre-row">{pills}</div>'
        f'<div class="cm-hero-title">{title_safe}</div>'
        f'<div class="cm-hero-overview">{overview_safe}</div>'
        f'<div class="cm-hero-stats">'
        f'<span><div class="cm-stat-label">Year</div><div class="cm-stat-val">{year_safe}</div></span>'
        f'{rating_html}'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)   # close .cm-hero


# ─────────────────────────────────────────────
# COMPONENT: Section header
# ─────────────────────────────────────────────
def section_header(title: str, label: str = ""):
    lbl = f'<span class="cm-section-lbl">{label}</span>' if label else ""
    st.markdown(
        f'<div class="cm-section"><h2>{title}</h2>'
        f'<div class="cm-section-div"></div>{lbl}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# COMPONENT: Movie grid
# ─────────────────────────────────────────────
PLACEHOLDER = "https://placehold.co/300x450/141420/555577?text=No+Poster"

def render_movie_grid(movies: List[Dict], cols: int = 6, show_score: bool = False):
    if not movies:
        st.markdown(
            '<div class="cm-empty"><div class="ei">🎬</div>'
            '<h3>No movies found</h3><p>Try a different search or category.</p></div>',
            unsafe_allow_html=True,
        )
        return

    flat = [normalise(m) for m in movies]

    for row_start in range(0, len(flat), cols):
        row     = flat[row_start: row_start + cols]
        columns = st.columns(cols, gap="small")

        for ci, movie in enumerate(row):
            with columns[ci]:
                title   = movie["title"]
                poster  = movie["poster_url"] or PLACEHOLDER
                year    = (movie["release_date"] or "")[:4] or "—"
                rating  = movie["vote_average"]
                score   = movie["score"]
                tmdb_id = movie["tmdb_id"]

                # Card top wrapper
                st.markdown('<div class="cm-card">', unsafe_allow_html=True)

                # Native image — Streamlit controls the img element
                st.image(poster, width=None)

                # Card body: single atomic HTML block (fully closed)
                rating_str = f"★ {rating:.1f}" if rating else "—"
                score_span = (
                    f'<span class="cm-score">{score:.2f}</span>'
                    if show_score and score is not None else ""
                )
                st.markdown(
                    f'<div class="cm-card-body">'
                    f'<div class="cm-card-title">{safe_text(title)}</div>'
                    f'<div class="cm-card-meta">'
                    f'<span class="cm-card-year">{year}</span>'
                    f'<span class="cm-card-rating">{rating_str}</span>'
                    f'{score_span}'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Details button
                if tmdb_id:
                    if st.button("Details", key=f"btn_{tmdb_id}_{row_start}_{ci}"):
                        st.session_state["selected_tmdb_id"] = int(tmdb_id)
                        st.session_state["selected_title"]   = title
                        st.session_state["goto_page"]        = "Details"
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)   # close .cm-card


# ─────────────────────────────────────────────
# TFIDF RECS — fetch posters in parallel
# Calls the fast /recommend/tfidf endpoint (no TMDB inside),
# then fans out poster fetches concurrently so it's ~1 round-trip
# instead of 12 sequential ones.
# ─────────────────────────────────────────────
def build_tfidf_cards(query: str, top_n: int = 12) -> List[Dict]:
    """
    1. Call /recommend/tfidf  →  list of {title, score}
    2. Fan-out parallel TMDB searches for posters (max 6 workers)
    3. Return merged list ready for render_movie_grid
    """
    recs = get_tfidf_recs(query, top_n=top_n)
    if not recs:
        return []

    def fetch_one(item: dict) -> dict:
        t   = item.get("title", "")
        scr = item.get("score", 0.0)
        m   = tmdb_search_first(t)
        if m:
            return {
                "title":        m.get("title") or t,
                "poster_url":   f"TMDB_IMAGE_BASE_URL{m['poster_path']}"
                                if m.get("poster_path") else None,
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
                "tmdb_id":      m.get("id"),
                "score":        scr,
            }
        return {"title": t, "poster_url": None, "release_date": None,
                "vote_average": None, "tmdb_id": None, "score": scr}

    cards = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_one, item): item for item in recs}
        for fut in as_completed(futures):
            try:
                cards.append(fut.result())
            except Exception:
                pass

    # Re-sort by score (parallel futures complete out-of-order)
    cards.sort(key=lambda x: x.get("score") or 0, reverse=True)
    return cards


# ─────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────
def page_home():
    cat_map = {
        "🔥 Trending":    "trending",
        "⭐ Top Rated":   "top_rated",
        "🎬 Now Playing": "now_playing",
        "📅 Upcoming":    "upcoming",
        "🍿 Popular":     "popular",
    }
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<h1 class="cm-page-title">Discover Films</h1>', unsafe_allow_html=True)
        st.markdown('<p class="cm-page-sub">Find your next watch from the world\'s best movies</p>',
                    unsafe_allow_html=True)
    with c2:
        cat_label = st.selectbox("", list(cat_map.keys()), label_visibility="hidden")

    with st.spinner("Loading movies…"):
        movies = get_home_feed(cat_map[cat_label], limit=24)
    if not movies:
        return

    hero = movies[0]
    if hero.get("poster_url"):
        render_hero(
            backdrop_url=hero["poster_url"].replace("/w500/", "/w1280/"),
            title=hero.get("title", ""),
            overview="",
            genres=[],
            year=(hero.get("release_date") or "")[:4],
            rating=hero.get("vote_average"),
            height=380,
        )

    section_header(f"{cat_label.split(' ', 1)[1]} Movies", f"{len(movies)} films")
    render_movie_grid(movies[1:], cols=6)


def page_search():
    st.markdown('<h1 class="cm-page-title">Search &amp; Discover</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cm-page-sub">Search for any film to get TF-IDF and genre-based recommendations</p>',
                unsafe_allow_html=True)

    c1, c2 = st.columns([5, 1])
    with c1:
        query = st.text_input("", placeholder="e.g. The Dark Knight, Inception…",
                              label_visibility="hidden", key="search_input")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        do_search = st.button("Search", use_container_width=True)

    if not (query and (do_search or st.session_state.get("last_search") == query)):
        st.markdown(
            '<div class="cm-empty" style="margin-top:60px;">'
            '<div class="ei">🔍</div>'
            '<h3>Search for a film to get started</h3>'
            '<p>Type a movie title above and press Search.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    st.session_state["last_search"] = query

    # ── TMDB search grid ──
    section_header("Search Results", "TMDB")
    with st.spinner("Searching TMDB…"):
        raw = search_movies(query)
    tmdb_first_id = None
    if raw and raw.get("results"):
        results = raw["results"]
        if results:
            tmdb_first_id = results[0].get("id")
        cards = [
            {
                "title":        m.get("title", ""),
                "poster_url":   f"TMDB_IMAGE_BASE_URL{m['poster_path']}"
                                if m.get("poster_path") else None,
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
                "tmdb_id":      m.get("id"),
            }
            for m in results[:12]
        ]
        render_movie_grid(cards, cols=6)

    # ── Recommendations: kick off both fetches in parallel ──
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("AI Recommendations", "TF-IDF + Genre")

    with st.spinner("Building recommendations… (this may take a few seconds)"):
        tfidf_cards = None
        genre_cards = None

        def _fetch_tfidf():
            return build_tfidf_cards(query, top_n=12)

        def _fetch_genre():
            if tmdb_first_id:
                return get_genre_recs(tmdb_first_id, limit=12)
            return []

        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_tfidf = pool.submit(_fetch_tfidf)
            fut_genre = pool.submit(_fetch_genre)
            tfidf_cards = fut_tfidf.result()
            genre_cards = fut_genre.result() or []

    # Hero for the best match
    if tmdb_first_id:
        details = get_movie_details(tmdb_first_id)
        if details and details.get("backdrop_url"):
            render_hero(
                backdrop_url=details["backdrop_url"],
                title=details.get("title", ""),
                overview=details.get("overview", ""),
                genres=details.get("genres", []),
                year=(details.get("release_date") or "")[:4],
                height=280,
            )

    tab1, tab2 = st.tabs(["🧠  Content-Based (TF-IDF)", "🎭  Same Genre"])
    with tab1:
        if tfidf_cards:
            render_movie_grid(tfidf_cards, cols=6, show_score=True)
        else:
            st.markdown(
                '<div class="cm-empty"><div class="ei">🤔</div>'
                '<h3>No TF-IDF matches</h3>'
                '<p>This title may not be in the local dataset.</p></div>',
                unsafe_allow_html=True,
            )
    with tab2:
        if genre_cards:
            render_movie_grid(genre_cards, cols=6)
        else:
            st.markdown(
                '<div class="cm-empty"><div class="ei">🎭</div>'
                '<h3>No genre recommendations</h3>'
                '<p>Could not find genre data for this film.</p></div>',
                unsafe_allow_html=True,
            )


def page_details():
    tmdb_id        = st.session_state.get("selected_tmdb_id")
    selected_title = st.session_state.get("selected_title", "")

    if not tmdb_id:
        st.markdown(
            '<div class="cm-empty" style="margin-top:80px;">'
            '<div class="ei">🎬</div><h3>No film selected</h3>'
            '<p>Click "Details" on any movie card to open this page.</p></div>',
            unsafe_allow_html=True,
        )
        return

    with st.spinner("Loading film…"):
        def _det():  return get_movie_details(tmdb_id)
        def _tfidf(): return build_tfidf_cards(selected_title, top_n=12) if selected_title else []
        def _genre(): return get_genre_recs(tmdb_id, limit=12)

        with ThreadPoolExecutor(max_workers=3) as pool:
            f_det   = pool.submit(_det)
            f_tfidf = pool.submit(_tfidf)
            f_genre = pool.submit(_genre)
            details    = f_det.result()
            tfidf_recs = f_tfidf.result() or []
            genre_recs = f_genre.result() or []

    if not details:
        st.error("Could not load movie details.")
        return

    if details.get("backdrop_url"):
        render_hero(
            backdrop_url=details["backdrop_url"],
            title=details.get("title", ""),
            overview=details.get("overview", ""),
            genres=details.get("genres", []),
            year=(details.get("release_date") or "")[:4],
            height=460,
        )

    col_poster, col_info = st.columns([1, 3], gap="large")
    with col_poster:
        if details.get("poster_url"):
            st.image(details["poster_url"], width=None)

    with col_info:
        year       = (details.get("release_date") or "")[:4]
        genres_str = " · ".join(g["name"] for g in details.get("genres", []))
        overview   = safe_text(details.get("overview") or "No overview available.")

        st.markdown(f'<div class="cm-detail-title">{safe_text(details.get("title",""))}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<p style="color:#9090B0;font-size:13px;margin-bottom:14px;">{genres_str}</p>',
                    unsafe_allow_html=True)
        st.markdown(f'<p class="cm-detail-overview">{overview}</p>', unsafe_allow_html=True)

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(
                f'<div class="cm-stat-card">'
                f'<div class="cm-stat-card-val">{year}</div>'
                f'<div class="cm-stat-card-label">Release Year</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with sc2:
            rd = safe_text(details.get("release_date", "Unknown"))
            st.markdown(
                f'<div class="cm-stat-card">'
                f'<div class="cm-stat-card-val" style="font-size:17px;">{rd}</div>'
                f'<div class="cm-stat-card-label">Release Date</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if tfidf_recs:
        section_header("Because You Liked This", "TF-IDF Content Matching")
        render_movie_grid(tfidf_recs, cols=6, show_score=True)
    if genre_recs:
        section_header("More in This Genre", "TMDB Discovery")
        render_movie_grid(genre_recs, cols=6)


def page_trending():
    st.markdown('<h1 class="cm-page-title">Trending Today</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cm-page-sub">What the world is watching right now</p>', unsafe_allow_html=True)
    with st.spinner("Loading…"):
        movies = get_home_feed("trending", limit=24)
    if movies:
        render_movie_grid(movies, cols=6)


def page_top_rated():
    st.markdown('<h1 class="cm-page-title">Top Rated</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cm-page-sub">The all-time greats, as rated by audiences worldwide</p>', unsafe_allow_html=True)
    with st.spinner("Loading…"):
        movies = get_home_feed("top_rated", limit=24)
    if movies:
        render_movie_grid(movies, cols=6)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
page_map = {
    "🏠  Home":      "Home",
    "🔍  Search":    "Search",
    "🔥  Trending":  "Trending",
    "⭐  Top Rated": "Top Rated",
    "🎬  Details":   "Details",
}

with st.sidebar:
    st.markdown(
        '<div class="nav-brand"><h1>CineMatch</h1><p>Film Discovery Engine</p></div>',
        unsafe_allow_html=True,
    )
    api_ok = health_check()
    sc, st_txt = ("#4CAF50", "API Connected") if api_ok else ("#E53935", "API Offline")
    st.markdown(
        f'<p style="padding:6px 20px 12px;font-size:11px;color:{sc};">● {st_txt}</p>',
        unsafe_allow_html=True,
    )
    nav = st.radio("Navigation", list(page_map.keys()), key="nav", label_visibility="hidden")
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.markdown(
        '<p style="padding:8px 20px;font-size:10px;color:#3A3A5A;letter-spacing:0.5px;">POWERED BY TMDB &amp; TF-IDF</p>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
goto         = st.session_state.pop("goto_page", None)
current_page = goto if goto else page_map[nav]

if current_page == "Home":        page_home()
elif current_page == "Search":    page_search()
elif current_page == "Trending":  page_trending()
elif current_page == "Top Rated": page_top_rated()
elif current_page == "Details":   page_details()