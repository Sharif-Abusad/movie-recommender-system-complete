# # # # import requests
# # # # import streamlit as st

# # # # # =============================
# # # # # CONFIG
# # # # # =============================
# # # # API_BASE =  "http://127.0.0.1:8000"
# # # # TMDB_IMG = "https://image.tmdb.org/t/p/w500"

# # # # st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# # # # # =============================
# # # # # STYLES (minimal modern)
# # # # # =============================
# # # # st.markdown(
# # # #     """
# # # # <style>
# # # # .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px; }
# # # # .small-muted { color:#6b7280; font-size: 0.92rem; }
# # # # .movie-title { font-size: 0.9rem; line-height: 1.15rem; height: 2.3rem; overflow: hidden; }
# # # # .card { border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; padding: 14px; background: rgba(255,255,255,0.7); }
# # # # </style>
# # # # """,
# # # #     unsafe_allow_html=True,
# # # # )

# # # # # =============================
# # # # # STATE + ROUTING (single-file pages)
# # # # # =============================
# # # # if "view" not in st.session_state:
# # # #     st.session_state.view = "home"  # home | details
# # # # if "selected_tmdb_id" not in st.session_state:
# # # #     st.session_state.selected_tmdb_id = None

# # # # qp_view = st.query_params.get("view")
# # # # qp_id = st.query_params.get("id")
# # # # if qp_view in ("home", "details"):
# # # #     st.session_state.view = qp_view
# # # # if qp_id:
# # # #     try:
# # # #         st.session_state.selected_tmdb_id = int(qp_id)
# # # #         st.session_state.view = "details"
# # # #     except:
# # # #         pass


# # # # def goto_home():
# # # #     st.session_state.view = "home"
# # # #     st.query_params["view"] = "home"
# # # #     if "id" in st.query_params:
# # # #         del st.query_params["id"]
# # # #     st.rerun()


# # # # def goto_details(tmdb_id: int):
# # # #     st.session_state.view = "details"
# # # #     st.session_state.selected_tmdb_id = int(tmdb_id)
# # # #     st.query_params["view"] = "details"
# # # #     st.query_params["id"] = str(int(tmdb_id))
# # # #     st.rerun()


# # # # # =============================
# # # # # API HELPERS
# # # # # =============================
# # # # @st.cache_data(ttl=30)  # short cache for autocomplete
# # # # def api_get_json(path: str, params: dict | None = None):
# # # #     try:
# # # #         r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
# # # #         print(r.json())
# # # #         if r.status_code >= 400:
# # # #             return None, f"HTTP {r.status_code}: {r.text[:300]}"
# # # #         return r.json(), None
# # # #     except Exception as e:
# # # #         return None, f"Request failed: {e}"


# # # # def poster_grid(cards, cols=6, key_prefix="grid"):
# # # #     if not cards:
# # # #         st.info("No movies to show.")
# # # #         return

# # # #     rows = (len(cards) + cols - 1) // cols
# # # #     idx = 0
# # # #     for r in range(rows):
# # # #         colset = st.columns(cols)
# # # #         for c in range(cols):
# # # #             if idx >= len(cards):
# # # #                 break
# # # #             m = cards[idx]
# # # #             idx += 1

# # # #             tmdb_id = m.get("tmdb_id")
# # # #             title = m.get("title", "Untitled")
# # # #             poster = m.get("poster_url")

# # # #             with colset[c]:
# # # #                 if poster:
# # # #                     st.image(poster, use_column_width=True)
# # # #                 else:
# # # #                     st.markdown("🖼️")

# # # #                 # Only show Open button if we have a tmdb_id
# # # #                 if tmdb_id:
# # # #                     if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
# # # #                         goto_details(tmdb_id)
# # # #                 else:
# # # #                     st.caption("No link")  # ← graceful fallback

# # # #                 st.markdown(
# # # #                     f"<div class='movie-title'>{title}</div>",
# # # #                     unsafe_allow_html=True
# # # #                 )

# # # # def to_cards_from_tfidf_items(tfidf_items):
# # # #     cards = []
# # # #     for x in tfidf_items or []:
# # # #         tmdb = x.get("tmdb") or {}
# # # #         tmdb_id = tmdb.get("tmdb_id")
# # # #         title = tmdb.get("title") or x.get("title") or "Untitled"
# # # #         poster_url = tmdb.get("poster_url")  # None is fine, grid handles it

# # # #         if tmdb_id:
# # # #             cards.append({
# # # #                 "tmdb_id": tmdb_id,
# # # #                 "title": title,
# # # #                 "poster_url": poster_url,
# # # #             })
# # # #         else:
# # # #             # Still show the movie, just without a clickable poster
# # # #             cards.append({
# # # #                 "tmdb_id": None,
# # # #                 "title": title,
# # # #                 "poster_url": None,
# # # #             })
# # # #     return cards


# # # # # =============================
# # # # # IMPORTANT: Robust TMDB search parsing
# # # # # Supports BOTH API shapes:
# # # # # 1) raw TMDB: {"results":[{id,title,poster_path,...}]}
# # # # # 2) list cards: [{tmdb_id,title,poster_url,...}]
# # # # # =============================
# # # # def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
# # # #     """
# # # #     Returns:
# # # #       suggestions: list[(label, tmdb_id)]
# # # #       cards: list[{tmdb_id,title,poster_url}]
# # # #     """
# # # #     keyword_l = keyword.strip().lower()

# # # #     # A) If API returns dict with 'results'
# # # #     if isinstance(data, dict) and "results" in data:
# # # #         raw = data.get("results") or []
# # # #         raw_items = []
# # # #         for m in raw:
# # # #             title = (m.get("title") or "").strip()
# # # #             tmdb_id = m.get("id")
# # # #             poster_path = m.get("poster_path")
# # # #             if not title or not tmdb_id:
# # # #                 continue
# # # #             raw_items.append(
# # # #                 {
# # # #                     "tmdb_id": int(tmdb_id),
# # # #                     "title": title,
# # # #                     "poster_url": f"{TMDB_IMG}{poster_path}" if poster_path else None,
# # # #                     "release_date": m.get("release_date", ""),
# # # #                 }
# # # #             )

# # # #     # B) If API returns already as list
# # # #     elif isinstance(data, list):
# # # #         raw_items = []
# # # #         for m in data:
# # # #             # might be {tmdb_id,title,poster_url}
# # # #             tmdb_id = m.get("tmdb_id") or m.get("id")
# # # #             title = (m.get("title") or "").strip()
# # # #             poster_url = m.get("poster_url")
# # # #             if not title or not tmdb_id:
# # # #                 continue
# # # #             raw_items.append(
# # # #                 {
# # # #                     "tmdb_id": int(tmdb_id),
# # # #                     "title": title,
# # # #                     "poster_url": poster_url,
# # # #                     "release_date": m.get("release_date", ""),
# # # #                 }
# # # #             )
# # # #     else:
# # # #         return [], []

# # # #     # Word-match filtering (contains)
# # # #     matched = [x for x in raw_items if keyword_l in x["title"].lower()]

# # # #     # If nothing matched, fallback to raw list (so never blank)
# # # #     final_list = matched if matched else raw_items

# # # #     # Suggestions = top 10 labels
# # # #     suggestions = []
# # # #     for x in final_list[:10]:
# # # #         year = (x.get("release_date") or "")[:4]
# # # #         label = f"{x['title']} ({year})" if year else x["title"]
# # # #         suggestions.append((label, x["tmdb_id"]))

# # # #     # Cards = top N
# # # #     cards = [
# # # #         {"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]}
# # # #         for x in final_list[:limit]
# # # #     ]
# # # #     return suggestions, cards


# # # # # =============================
# # # # # SIDEBAR (clean)
# # # # # =============================
# # # # with st.sidebar:
# # # #     st.markdown("## 🎬 Menu")
# # # #     if st.button("🏠 Home"):
# # # #         goto_home()

# # # #     st.markdown("---")
# # # #     st.markdown("### 🏠 Home Feed (only home)")
# # # #     home_category = st.selectbox(
# # # #         "Category",
# # # #         ["trending", "popular", "top_rated", "now_playing", "upcoming"],
# # # #         index=0,
# # # #     )
# # # #     grid_cols = st.slider("Grid columns", 4, 8, 6)

# # # # # =============================
# # # # # HEADER
# # # # # =============================
# # # # st.title("🎬 Movie Recommender")
# # # # st.markdown(
# # # #     "<div class='small-muted'>Type keyword → dropdown suggestions + matching results → open → details + recommendations</div>",
# # # #     unsafe_allow_html=True,
# # # # )
# # # # st.divider()

# # # # # ==========================================================
# # # # # VIEW: HOME
# # # # # ==========================================================
# # # # if st.session_state.view == "home":
# # # #     typed = st.text_input(
# # # #         "Search by movie title (keyword)", placeholder="Type: avenger, batman, love..."
# # # #     )

# # # #     st.divider()

# # # #     # SEARCH MODE (Autocomplete + word-match results)
# # # #     if typed.strip():
# # # #         if len(typed.strip()) < 2:
# # # #             st.caption("Type at least 2 characters for suggestions.")
# # # #         else:
# # # #             data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})

# # # #             if err or data is None:
# # # #                 st.error(f"Search failed: {err}")
# # # #             else:
# # # #                 suggestions, cards = parse_tmdb_search_to_cards(
# # # #                     data, typed.strip(), limit=24
# # # #                 )

# # # #                 # Dropdown
# # # #                 if suggestions:
# # # #                     labels = ["-- Select a movie --"] + [s[0] for s in suggestions]
# # # #                     selected = st.selectbox("Suggestions", labels, index=0)

# # # #                     if selected != "-- Select a movie --":
# # # #                         # map label -> id
# # # #                         label_to_id = {s[0]: s[1] for s in suggestions}
# # # #                         goto_details(label_to_id[selected])
# # # #                 else:
# # # #                     st.info("No suggestions found. Try another keyword.")

# # # #                 st.markdown("### Results")
# # # #                 poster_grid(cards, cols=grid_cols, key_prefix="search_results")

# # # #         st.stop()

# # # #     # HOME FEED MODE
# # # #     st.markdown(f"### 🏠 Home — {home_category.replace('_',' ').title()}")

# # # #     home_cards, err = api_get_json(
# # # #         "/home", params={"category": home_category, "limit": 24}
# # # #     )
# # # #     if err or not home_cards:
# # # #         st.error(f"Home feed failed: {err or 'Unknown error'}")
# # # #         st.stop()

# # # #     poster_grid(home_cards, cols=grid_cols, key_prefix="home_feed")

# # # # # ==========================================================
# # # # # VIEW: DETAILS
# # # # # ==========================================================
# # # # elif st.session_state.view == "details":
# # # #     tmdb_id = st.session_state.selected_tmdb_id
# # # #     if not tmdb_id:
# # # #         st.warning("No movie selected.")
# # # #         if st.button("← Back to Home"):
# # # #             goto_home()
# # # #         st.stop()

# # # #     # Top bar
# # # #     a, b = st.columns([3, 1])
# # # #     with a:
# # # #         st.markdown("### 📄 Movie Details")
# # # #     with b:
# # # #         if st.button("← Back to Home"):
# # # #             goto_home()

# # # #     # Details (your FastAPI safe route)
# # # #     data, err = api_get_json(f"/movie/id/{tmdb_id}")
# # # #     if err or not data:
# # # #         st.error(f"Could not load details: {err or 'Unknown error'}")
# # # #         st.stop()

# # # #     # Layout: Poster LEFT, Details RIGHT
# # # #     left, right = st.columns([1, 2.4], gap="large")

# # # #     with left:
# # # #         st.markdown("<div class='card'>", unsafe_allow_html=True)
# # # #         if data.get("poster_url"):
# # # #             st.image(data["poster_url"], use_column_width=True)
# # # #         else:
# # # #             st.write("🖼️ No poster")
# # # #         st.markdown("</div>", unsafe_allow_html=True)

# # # #     with right:
# # # #         st.markdown("<div class='card'>", unsafe_allow_html=True)
# # # #         st.markdown(f"## {data.get('title','')}")
# # # #         release = data.get("release_date") or "-"
# # # #         genres = ", ".join([g["name"] for g in data.get("genres", [])]) or "-"
# # # #         st.markdown(
# # # #             f"<div class='small-muted'>Release: {release}</div>", unsafe_allow_html=True
# # # #         )
# # # #         st.markdown(
# # # #             f"<div class='small-muted'>Genres: {genres}</div>", unsafe_allow_html=True
# # # #         )
# # # #         st.markdown("---")
# # # #         st.markdown("### Overview")
# # # #         st.write(data.get("overview") or "No overview available.")
# # # #         st.markdown("</div>", unsafe_allow_html=True)

# # # #     if data.get("backdrop_url"):
# # # #         st.markdown("#### Backdrop")
# # # #         st.image(data["backdrop_url"], use_column_width=True)

# # # #     st.divider()
# # # #     st.markdown("### ✅ Recommendations")

# # # #     # Recommendations (TF-IDF + Genre) via your bundle endpoint
# # # #     title = (data.get("title") or "").strip()
# # # #     if title:
# # # #         bundle, err2 = api_get_json(
# # # #             "/movie/search",
# # # #             params={"query": title, "tfidf_top_n": 12, "genre_limit": 12},
# # # #         )
# # # #         print(bundle)
# # # #         if not err2 and bundle:
# # # #             tfidf_items = bundle.get("tfidf_recommendations", [])
            
# # # #             # Temporary debug — remove later
# # # #             st.write(f"TF-IDF items received: {len(tfidf_items)}")
# # # #             st.write(f"Items with TMDB data: {sum(1 for x in tfidf_items if x.get('tmdb'))}")
# # # #             st.markdown("#### 🔎 Similar Movies (TF-IDF)")
# # # #             poster_grid(
# # # #                 to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
# # # #                 cols=grid_cols,
# # # #                 key_prefix="details_tfidf",
# # # #             )

# # # #             st.markdown("#### 🎭 More Like This (Genre)")
# # # #             poster_grid(
# # # #                 bundle.get("genre_recommendations", []),
# # # #                 cols=grid_cols,
# # # #                 key_prefix="details_genre",
# # # #             )
# # # #         else:
# # # #             st.info("Showing Genre recommendations (fallback).")
# # # #             genre_only, err3 = api_get_json(
# # # #                 "/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 18}
# # # #             )
# # # #             if not err3 and genre_only:
# # # #                 poster_grid(
# # # #                     genre_only, cols=grid_cols, key_prefix="details_genre_fallback"
# # # #                 )
# # # #             else:
# # # #                 st.warning("No recommendations available right now.")
# # # #     else:
# # # #         st.warning("No title available to compute recommendations.")
# # # import streamlit as st
# # # import requests
# # # from typing import Optional, List, Dict, Any

# # # # ─────────────────────────────────────────────
# # # # CONFIG
# # # # ─────────────────────────────────────────────
# # # API_BASE = "http://localhost:8000"

# # # st.set_page_config(
# # #     page_title="CineMatch",
# # #     page_icon="🎬",
# # #     layout="wide",
# # #     initial_sidebar_state="expanded",
# # # )

# # # # ─────────────────────────────────────────────
# # # # GLOBAL CSS
# # # # ─────────────────────────────────────────────
# # # st.markdown("""
# # # <style>
# # # @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700;900&display=swap');

# # # /* ── Reset & Base ── */
# # # *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

# # # html, body, [data-testid="stApp"] {
# # #     background: #0A0A0F !important;
# # #     color: #E8E8F0 !important;
# # #     font-family: 'Inter', sans-serif;
# # # }

# # # /* Hide Streamlit chrome */
# # # #MainMenu, footer, header, [data-testid="stToolbar"],
# # # [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

# # # /* ── Sidebar ── */
# # # [data-testid="stSidebar"] {
# # #     background: #0D0D18 !important;
# # #     border-right: 1px solid #1E1E2E !important;
# # #     padding-top: 0 !important;
# # # }
# # # [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

# # # /* ── Sidebar nav items ── */
# # # .nav-brand {
# # #     padding: 28px 20px 24px;
# # #     border-bottom: 1px solid #1E1E2E;
# # #     margin-bottom: 12px;
# # # }
# # # .nav-brand h1 {
# # #     font-family: 'Playfair Display', serif;
# # #     font-size: 26px;
# # #     font-weight: 900;
# # #     background: linear-gradient(135deg, #F5A623, #FF6B35);
# # #     -webkit-background-clip: text;
# # #     -webkit-text-fill-color: transparent;
# # #     background-clip: text;
# # #     letter-spacing: -0.5px;
# # # }
# # # .nav-brand p { color: #6B6B8A; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }

# # # /* ── Radio as nav ── */
# # # [data-testid="stSidebar"] .stRadio > label { display: none; }
# # # [data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
# # # [data-testid="stSidebar"] .stRadio > div > label {
# # #     display: flex !important;
# # #     align-items: center !important;
# # #     gap: 10px !important;
# # #     padding: 10px 20px !important;
# # #     border-radius: 8px !important;
# # #     cursor: pointer !important;
# # #     font-size: 14px !important;
# # #     font-weight: 500 !important;
# # #     color: #9090B0 !important;
# # #     transition: all 0.15s ease !important;
# # #     background: transparent !important;
# # #     border: none !important;
# # #     margin: 1px 8px !important;
# # #     width: calc(100% - 16px) !important;
# # # }
# # # [data-testid="stSidebar"] .stRadio > div > label:hover {
# # #     background: #1E1E2E !important;
# # #     color: #E8E8F0 !important;
# # # }
# # # [data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"] span:first-child { display: none !important; }

# # # /* Active nav item */
# # # [data-testid="stSidebar"] .stRadio [aria-checked="true"] {
# # #     background: linear-gradient(135deg, rgba(245,166,35,0.15), rgba(255,107,53,0.08)) !important;
# # #     color: #F5A623 !important;
# # #     border-left: 2px solid #F5A623 !important;
# # #     padding-left: 18px !important;
# # # }

# # # /* ── Main content area ── */
# # # .main .block-container {
# # #     padding: 0 !important;
# # #     max-width: 100% !important;
# # # }
# # # section[data-testid="stMain"] .block-container {
# # #     padding: 32px 40px !important;
# # #     max-width: 1400px !important;
# # # }

# # # /* ── Movie Cards ── */
# # # .movie-card {
# # #     background: #141420;
# # #     border-radius: 12px;
# # #     overflow: hidden;
# # #     transition: transform 0.2s ease, box-shadow 0.2s ease;
# # #     cursor: pointer;
# # #     border: 1px solid #1E1E2E;
# # #     height: 100%;
# # # }
# # # .movie-card:hover {
# # #     transform: translateY(-4px);
# # #     box-shadow: 0 12px 40px rgba(245, 166, 35, 0.15);
# # #     border-color: rgba(245,166,35,0.3);
# # # }
# # # .movie-card img {
# # #     width: 100%;
# # #     aspect-ratio: 2/3;
# # #     object-fit: cover;
# # #     display: block;
# # # }
# # # .movie-card-no-img {
# # #     width: 100%;
# # #     aspect-ratio: 2/3;
# # #     background: linear-gradient(145deg, #1E1E2E, #0D0D18);
# # #     display: flex;
# # #     align-items: center;
# # #     justify-content: center;
# # #     font-size: 40px;
# # # }
# # # .card-body { padding: 12px; }
# # # .card-title {
# # #     font-size: 13px;
# # #     font-weight: 600;
# # #     color: #E8E8F0;
# # #     line-height: 1.3;
# # #     margin-bottom: 6px;
# # #     display: -webkit-box;
# # #     -webkit-line-clamp: 2;
# # #     -webkit-box-orient: vertical;
# # #     overflow: hidden;
# # # }
# # # .card-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
# # # .card-year { font-size: 11px; color: #6B6B8A; }
# # # .card-rating {
# # #     display: flex;
# # #     align-items: center;
# # #     gap: 3px;
# # #     font-size: 11px;
# # #     font-weight: 600;
# # #     color: #F5A623;
# # # }
# # # .score-badge {
# # #     display: inline-block;
# # #     background: rgba(245,166,35,0.15);
# # #     border: 1px solid rgba(245,166,35,0.3);
# # #     color: #F5A623;
# # #     font-size: 10px;
# # #     font-weight: 700;
# # #     padding: 2px 7px;
# # #     border-radius: 20px;
# # #     letter-spacing: 0.3px;
# # # }

# # # /* ── Hero Section ── */
# # # .hero {
# # #     position: relative;
# # #     border-radius: 16px;
# # #     overflow: hidden;
# # #     margin-bottom: 40px;
# # # }
# # # .hero-backdrop {
# # #     width: 100%;
# # #     height: 420px;
# # #     object-fit: cover;
# # #     display: block;
# # # }
# # # .hero-overlay {
# # #     position: absolute;
# # #     inset: 0;
# # #     background: linear-gradient(90deg,
# # #         rgba(10,10,15,0.98) 0%,
# # #         rgba(10,10,15,0.85) 40%,
# # #         rgba(10,10,15,0.3) 70%,
# # #         transparent 100%
# # #     );
# # #     display: flex;
# # #     align-items: flex-end;
# # #     padding: 40px;
# # # }
# # # .hero-content { max-width: 520px; }
# # # .hero-genres { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
# # # .genre-pill {
# # #     background: rgba(245,166,35,0.15);
# # #     border: 1px solid rgba(245,166,35,0.4);
# # #     color: #F5A623;
# # #     font-size: 11px;
# # #     font-weight: 600;
# # #     padding: 3px 10px;
# # #     border-radius: 20px;
# # #     text-transform: uppercase;
# # #     letter-spacing: 0.8px;
# # # }
# # # .hero-title {
# # #     font-family: 'Playfair Display', serif;
# # #     font-size: 44px;
# # #     font-weight: 900;
# # #     color: #FFFFFF;
# # #     line-height: 1.1;
# # #     margin-bottom: 12px;
# # #     letter-spacing: -1px;
# # # }
# # # .hero-overview {
# # #     font-size: 14px;
# # #     color: #B0B0C8;
# # #     line-height: 1.6;
# # #     margin-bottom: 20px;
# # #     display: -webkit-box;
# # #     -webkit-line-clamp: 3;
# # #     -webkit-box-orient: vertical;
# # #     overflow: hidden;
# # # }
# # # .hero-stats { display: flex; align-items: center; gap: 20px; }
# # # .hero-stat { text-align: left; }
# # # .hero-stat-label { font-size: 10px; color: #6B6B8A; letter-spacing: 1px; text-transform: uppercase; }
# # # .hero-stat-value { font-size: 18px; font-weight: 700; color: #F5A623; }

# # # /* ── Section Headers ── */
# # # .section-header {
# # #     display: flex;
# # #     align-items: baseline;
# # #     gap: 16px;
# # #     margin-bottom: 20px;
# # #     margin-top: 40px;
# # # }
# # # .section-header h2 {
# # #     font-family: 'Playfair Display', serif;
# # #     font-size: 22px;
# # #     font-weight: 700;
# # #     color: #E8E8F0;
# # # }
# # # .section-divider {
# # #     flex: 1;
# # #     height: 1px;
# # #     background: linear-gradient(90deg, #1E1E2E, transparent);
# # # }
# # # .section-label {
# # #     font-size: 11px;
# # #     color: #6B6B8A;
# # #     letter-spacing: 1px;
# # #     text-transform: uppercase;
# # # }

# # # /* ── Search Bar ── */
# # # [data-testid="stTextInput"] > div > div > input {
# # #     background: #141420 !important;
# # #     border: 1px solid #2A2A40 !important;
# # #     border-radius: 10px !important;
# # #     color: #E8E8F0 !important;
# # #     padding: 14px 18px !important;
# # #     font-size: 16px !important;
# # #     font-family: 'Inter', sans-serif !important;
# # #     transition: border-color 0.2s ease !important;
# # # }
# # # [data-testid="stTextInput"] > div > div > input:focus {
# # #     border-color: #F5A623 !important;
# # #     box-shadow: 0 0 0 3px rgba(245,166,35,0.1) !important;
# # # }
# # # [data-testid="stTextInput"] > div > div > input::placeholder { color: #4A4A6A !important; }

# # # /* ── Selectbox ── */
# # # [data-testid="stSelectbox"] > div > div {
# # #     background: #141420 !important;
# # #     border: 1px solid #2A2A40 !important;
# # #     border-radius: 10px !important;
# # #     color: #E8E8F0 !important;
# # # }

# # # /* ── Buttons ── */
# # # .stButton > button {
# # #     background: linear-gradient(135deg, #F5A623, #FF6B35) !important;
# # #     color: #0A0A0F !important;
# # #     border: none !important;
# # #     border-radius: 10px !important;
# # #     font-weight: 700 !important;
# # #     font-size: 14px !important;
# # #     padding: 12px 28px !important;
# # #     transition: opacity 0.2s ease, transform 0.1s ease !important;
# # #     font-family: 'Inter', sans-serif !important;
# # #     letter-spacing: 0.2px !important;
# # # }
# # # .stButton > button:hover {
# # #     opacity: 0.9 !important;
# # #     transform: translateY(-1px) !important;
# # # }
# # # .stButton > button:active { transform: translateY(0) !important; }

# # # /* ── Page Title ── */
# # # .page-title {
# # #     font-family: 'Playfair Display', serif;
# # #     font-size: 32px;
# # #     font-weight: 900;
# # #     color: #FFFFFF;
# # #     margin-bottom: 6px;
# # #     letter-spacing: -0.5px;
# # # }
# # # .page-subtitle { font-size: 14px; color: #6B6B8A; margin-bottom: 32px; }

# # # /* ── Detail Page ── */
# # # .detail-poster {
# # #     border-radius: 12px;
# # #     overflow: hidden;
# # #     box-shadow: 0 20px 60px rgba(0,0,0,0.5);
# # # }
# # # .detail-poster img { width: 100%; display: block; }
# # # .detail-meta-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
# # # .detail-title {
# # #     font-family: 'Playfair Display', serif;
# # #     font-size: 38px;
# # #     font-weight: 900;
# # #     color: #FFFFFF;
# # #     line-height: 1.1;
# # #     margin-bottom: 12px;
# # #     letter-spacing: -1px;
# # # }
# # # .detail-overview { font-size: 15px; color: #B0B0C8; line-height: 1.7; margin-bottom: 24px; }
# # # .detail-stat-card {
# # #     background: #141420;
# # #     border: 1px solid #1E1E2E;
# # #     border-radius: 10px;
# # #     padding: 16px 20px;
# # #     text-align: center;
# # # }
# # # .detail-stat-val { font-size: 24px; font-weight: 700; color: #F5A623; }
# # # .detail-stat-label { font-size: 11px; color: #6B6B8A; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }

# # # /* ── Loading / Empty ── */
# # # .empty-state {
# # #     text-align: center;
# # #     padding: 80px 40px;
# # #     color: #4A4A6A;
# # # }
# # # .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
# # # .empty-state h3 { font-size: 18px; color: #6B6B8A; margin-bottom: 8px; }
# # # .empty-state p { font-size: 13px; }

# # # /* ── Tabs ── */
# # # [data-testid="stTabs"] [role="tablist"] {
# # #     border-bottom: 1px solid #1E1E2E !important;
# # #     gap: 0 !important;
# # #     background: transparent !important;
# # # }
# # # [data-testid="stTabs"] [role="tab"] {
# # #     color: #6B6B8A !important;
# # #     font-size: 13px !important;
# # #     font-weight: 500 !important;
# # #     padding: 10px 20px !important;
# # #     border: none !important;
# # #     background: transparent !important;
# # #     border-bottom: 2px solid transparent !important;
# # # }
# # # [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
# # #     color: #F5A623 !important;
# # #     border-bottom-color: #F5A623 !important;
# # # }
# # # [data-testid="stTabs"] [data-testid="stTabsContent"] { background: transparent !important; }

# # # /* ── Spinner ── */
# # # [data-testid="stSpinner"] { color: #F5A623 !important; }

# # # /* ── Scrollbar ── */
# # # ::-webkit-scrollbar { width: 6px; height: 6px; }
# # # ::-webkit-scrollbar-track { background: #0A0A0F; }
# # # ::-webkit-scrollbar-thumb { background: #2A2A40; border-radius: 3px; }
# # # ::-webkit-scrollbar-thumb:hover { background: #F5A623; }

# # # /* ── Dividers ── */
# # # hr { border-color: #1E1E2E !important; }
# # # </style>
# # # """, unsafe_allow_html=True)


# # # # ─────────────────────────────────────────────
# # # # API HELPERS
# # # # ─────────────────────────────────────────────
# # # def api_get(path: str, params: Dict = None) -> Optional[Any]:
# # #     try:
# # #         r = requests.get(f"{API_BASE}{path}", params=params or {}, timeout=20)
# # #         r.raise_for_status()
# # #         return r.json()
# # #     except requests.exceptions.ConnectionError:
# # #         st.error("⚠️ Cannot reach the backend API. Make sure the FastAPI server is running on localhost:8000.")
# # #         return None
# # #     except requests.exceptions.HTTPError as e:
# # #         st.error(f"API error: {e.response.status_code} — {e.response.text[:200]}")
# # #         return None
# # #     except Exception as e:
# # #         st.error(f"Unexpected error: {e}")
# # #         return None


# # # @st.cache_data(ttl=300)
# # # def get_home_feed(category: str, limit: int = 24):
# # #     return api_get("/home", {"category": category, "limit": limit})


# # # @st.cache_data(ttl=60)
# # # def search_movies(query: str, page: int = 1):
# # #     return api_get("/tmdb/search", {"query": query, "page": page})


# # # @st.cache_data(ttl=300)
# # # def get_search_bundle(query: str, tfidf_top_n: int = 12, genre_limit: int = 12):
# # #     return api_get("/movie/search", {"query": query, "tfidf_top_n": tfidf_top_n, "genre_limit": genre_limit})


# # # @st.cache_data(ttl=300)
# # # def get_movie_details(tmdb_id: int):
# # #     return api_get(f"/movie/id/{tmdb_id}")


# # # def health_check() -> bool:
# # #     try:
# # #         r = requests.get(f"{API_BASE}/health", timeout=5)
# # #         return r.status_code == 200
# # #     except Exception:
# # #         return False


# # # # ─────────────────────────────────────────────
# # # # COMPONENT: Movie Card
# # # # ─────────────────────────────────────────────
# # # def movie_card_html(title: str, poster_url: Optional[str], year: Optional[str],
# # #                     rating: Optional[float], score: Optional[float] = None) -> str:
# # #     year_str = year[:4] if year else "—"
# # #     rating_html = (
# # #         f'<span class="card-rating">★ {rating:.1f}</span>'
# # #         if rating else '<span class="card-rating" style="color:#4A4A6A;">No rating</span>'
# # #     )
# # #     score_html = f'<span class="score-badge">{score:.2f}</span>' if score is not None else ""
# # #     img_html = (
# # #         f'<img src="{poster_url}" alt="{title}" loading="lazy" />'
# # #         if poster_url else '<div class="movie-card-no-img">🎬</div>'
# # #     )
# # #     return f"""
# # #     <div class="movie-card">
# # #         {img_html}
# # #         <div class="card-body">
# # #             <div class="card-title">{title}</div>
# # #             <div class="card-meta">
# # #                 <span class="card-year">{year_str}</span>
# # #                 <div style="display:flex;gap:6px;align-items:center;">
# # #                     {rating_html}
# # #                     {score_html}
# # #                 </div>
# # #             </div>
# # #         </div>
# # #     </div>
# # #     """


# # # def render_movie_grid(movies: List[Dict], cols: int = 6, show_score: bool = False):
# # #     if not movies:
# # #         st.markdown("""
# # #         <div class="empty-state">
# # #             <div class="icon">🎬</div>
# # #             <h3>No movies found</h3>
# # #             <p>Try a different search or category</p>
# # #         </div>""", unsafe_allow_html=True)
# # #         return

# # #     columns = st.columns(cols, gap="small")
# # #     for i, movie in enumerate(movies):
# # #         with columns[i % cols]:
# # #             score = None
# # #             if show_score and movie.get("score") is not None:
# # #                 score = movie["score"]

# # #             # Handle both TMDB card and TFIDFRecItem with nested tmdb
# # #             if "tmdb" in movie and movie["tmdb"]:
# # #                 tmdb_data = movie["tmdb"]
# # #                 m = {
# # #                     "title": movie.get("title", ""),
# # #                     "poster_url": tmdb_data.get("poster_url"),
# # #                     "release_date": tmdb_data.get("release_date"),
# # #                     "vote_average": tmdb_data.get("vote_average"),
# # #                     "tmdb_id": tmdb_data.get("tmdb_id"),
# # #                 }
# # #             else:
# # #                 m = movie

# # #             title = m.get("title", "Unknown")
# # #             poster_url = m.get("poster_url")
# # #             year = m.get("release_date")
# # #             rating = m.get("vote_average")
# # #             tmdb_id = m.get("tmdb_id") or (movie.get("tmdb", {}) or {}).get("tmdb_id")

# # #             html = movie_card_html(title, poster_url, year, rating, score)
# # #             st.markdown(html, unsafe_allow_html=True)

# # #             if tmdb_id and st.button("Details", key=f"card_{tmdb_id}_{i}", use_container_width=True):
# # #                 st.session_state["selected_tmdb_id"] = int(tmdb_id)
# # #                 st.session_state["selected_title"] = title
# # #                 st.session_state["page"] = "Details"
# # #                 st.rerun()


# # # # ─────────────────────────────────────────────
# # # # COMPONENT: Section Header
# # # # ─────────────────────────────────────────────
# # # def section_header(title: str, label: str = ""):
# # #     label_html = f'<span class="section-label">{label}</span>' if label else ""
# # #     st.markdown(f"""
# # #     <div class="section-header">
# # #         <h2>{title}</h2>
# # #         <div class="section-divider"></div>
# # #         {label_html}
# # #     </div>""", unsafe_allow_html=True)


# # # # ─────────────────────────────────────────────
# # # # PAGES
# # # # ─────────────────────────────────────────────
# # # def page_home():
# # #     # Category selector
# # #     cat_map = {
# # #         "🔥 Trending": "trending",
# # #         "⭐ Top Rated": "top_rated",
# # #         "🎬 Now Playing": "now_playing",
# # #         "📅 Upcoming": "upcoming",
# # #         "🍿 Popular": "popular",
# # #     }
# # #     cols = st.columns([3, 1])
# # #     with cols[0]:
# # #         st.markdown('<h1 class="page-title">Discover Films</h1>', unsafe_allow_html=True)
# # #         st.markdown('<p class="page-subtitle">Find your next watch from the world\'s best movies</p>', unsafe_allow_html=True)
# # #     with cols[1]:
# # #         cat_label = st.selectbox("Browse by", list(cat_map.keys()), label_visibility="hidden")

# # #     category = cat_map[cat_label]

# # #     with st.spinner("Loading movies..."):
# # #         movies = get_home_feed(category, limit=24)

# # #     if not movies:
# # #         return

# # #     # Hero — feature the first movie
# # #     hero = movies[0]
# # #     if hero.get("poster_url"):
# # #         poster = hero["poster_url"].replace("/w500/", "/w1280/")
# # #         year = hero.get("release_date", "")[:4]
# # #         rating = hero.get("vote_average", 0)
# # #         st.markdown(f"""
# # #         <div class="hero">
# # #             <img class="hero-backdrop" src="{poster}" alt="{hero['title']}" />
# # #             <div class="hero-overlay">
# # #                 <div class="hero-content">
# # #                     <div class="hero-genres">
# # #                         <span class="genre-pill">Featured</span>
# # #                     </div>
# # #                     <div class="hero-title">{hero['title']}</div>
# # #                     <div class="hero-stats">
# # #                         <div class="hero-stat">
# # #                             <div class="hero-stat-label">Rating</div>
# # #                             <div class="hero-stat-value">★ {rating:.1f}</div>
# # #                         </div>
# # #                         <div class="hero-stat">
# # #                             <div class="hero-stat-label">Year</div>
# # #                             <div class="hero-stat-value">{year}</div>
# # #                         </div>
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #         </div>""", unsafe_allow_html=True)

# # #     section_header(f"{cat_label.split(' ', 1)[1]} Movies", f"{len(movies)} films")
# # #     render_movie_grid(movies[1:], cols=6)


# # # def page_search():
# # #     st.markdown('<h1 class="page-title">Search & Discover</h1>', unsafe_allow_html=True)
# # #     st.markdown('<p class="page-subtitle">Search for any film to get personalized TF-IDF and genre recommendations</p>', unsafe_allow_html=True)

# # #     col1, col2 = st.columns([5, 1])
# # #     with col1:
# # #         query = st.text_input("", placeholder="Search for a movie... e.g. The Dark Knight", label_visibility="hidden")
# # #     with col2:
# # #         st.markdown("<br>", unsafe_allow_html=True)
# # #         search_btn = st.button("Search", use_container_width=True)

# # #     if query and (search_btn or st.session_state.get("last_search") == query):
# # #         st.session_state["last_search"] = query

# # #         # Quick multi-result search
# # #         section_header("Search Results", "TMDB")
# # #         with st.spinner("Searching..."):
# # #             raw = search_movies(query)

# # #         if raw and raw.get("results"):
# # #             results = raw["results"][:12]
# # #             cards = [
# # #                 {
# # #                     "title": m.get("title", ""),
# # #                     "poster_url": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get("poster_path") else None,
# # #                     "release_date": m.get("release_date"),
# # #                     "vote_average": m.get("vote_average"),
# # #                     "tmdb_id": m.get("id"),
# # #                 }
# # #                 for m in results
# # #             ]
# # #             render_movie_grid(cards, cols=6)

# # #         # Bundle: TF-IDF + Genre recommendations for best match
# # #         st.markdown("<br>", unsafe_allow_html=True)
# # #         section_header("Personalized Recommendations", "AI-powered")

# # #         with st.spinner("Getting recommendations..."):
# # #             bundle = get_search_bundle(query)

# # #         if bundle:
# # #             details = bundle.get("movie_details", {})
# # #             tfidf_recs = bundle.get("tfidf_recommendations", [])
# # #             genre_recs = bundle.get("genre_recommendations", [])

# # #             # Movie detail mini-hero
# # #             if details.get("backdrop_url"):
# # #                 bk = details["backdrop_url"]
# # #                 genres_html = "".join(
# # #                     f'<span class="genre-pill">{g["name"]}</span>'
# # #                     for g in details.get("genres", [])[:3]
# # #                 )
# # #                 year = (details.get("release_date") or "")[:4]
# # #                 st.markdown(f"""
# # #                 <div class="hero" style="margin-top:8px;">
# # #                     <img class="hero-backdrop" src="{bk}" style="height:280px;" />
# # #                     <div class="hero-overlay">
# # #                         <div class="hero-content">
# # #                             <div class="hero-genres">{genres_html}</div>
# # #                             <div class="hero-title" style="font-size:30px;">{details.get('title','')}</div>
# # #                             <div class="hero-overview">{details.get('overview','')}</div>
# # #                         </div>
# # #                     </div>
# # #                 </div>""", unsafe_allow_html=True)

# # #             tab1, tab2 = st.tabs(["🧠  Content-Based (TF-IDF)", "🎭  Same Genre"])

# # #             with tab1:
# # #                 if tfidf_recs:
# # #                     render_movie_grid(tfidf_recs, cols=6, show_score=True)
# # #                 else:
# # #                     st.markdown("""<div class="empty-state">
# # #                         <div class="icon">🤔</div>
# # #                         <h3>No TF-IDF recommendations</h3>
# # #                         <p>This title may not be in the local dataset</p>
# # #                     </div>""", unsafe_allow_html=True)

# # #             with tab2:
# # #                 if genre_recs:
# # #                     render_movie_grid(genre_recs, cols=6)
# # #                 else:
# # #                     st.markdown("""<div class="empty-state">
# # #                         <div class="icon">🎭</div>
# # #                         <h3>No genre recommendations</h3>
# # #                         <p>Could not find genre data for this film</p>
# # #                     </div>""", unsafe_allow_html=True)
# # #     else:
# # #         st.markdown("""
# # #         <div class="empty-state" style="margin-top:60px;">
# # #             <div class="icon">🔍</div>
# # #             <h3>Search for a film to get started</h3>
# # #             <p>Type a movie title above and hit Search to see results and AI recommendations</p>
# # #         </div>""", unsafe_allow_html=True)


# # # def page_details():
# # #     tmdb_id = st.session_state.get("selected_tmdb_id")
# # #     selected_title = st.session_state.get("selected_title", "")

# # #     if not tmdb_id:
# # #         st.markdown("""<div class="empty-state" style="margin-top:80px;">
# # #             <div class="icon">🎬</div>
# # #             <h3>No film selected</h3>
# # #             <p>Go to Search or Browse and click "Details" on any movie card</p>
# # #         </div>""", unsafe_allow_html=True)
# # #         return

# # #     with st.spinner("Loading film details..."):
# # #         details = get_movie_details(tmdb_id)
# # #         bundle = get_search_bundle(selected_title) if selected_title else None

# # #     if not details:
# # #         st.error("Could not load movie details.")
# # #         return

# # #     # Full backdrop hero
# # #     if details.get("backdrop_url"):
# # #         genres_html = "".join(
# # #             f'<span class="genre-pill">{g["name"]}</span>'
# # #             for g in details.get("genres", [])
# # #         )
# # #         year = (details.get("release_date") or "")[:4]
# # #         overview = details.get("overview", "")
# # #         st.markdown(f"""
# # #         <div class="hero">
# # #             <img class="hero-backdrop" src="{details['backdrop_url']}" style="height:460px;" />
# # #             <div class="hero-overlay">
# # #                 <div class="hero-content">
# # #                     <div class="hero-genres">{genres_html}</div>
# # #                     <div class="hero-title">{details.get('title','')}</div>
# # #                     <div class="hero-overview">{overview}</div>
# # #                     <div class="hero-stats">
# # #                         <div class="hero-stat">
# # #                             <div class="hero-stat-label">Year</div>
# # #                             <div class="hero-stat-value">{year}</div>
# # #                         </div>
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #         </div>""", unsafe_allow_html=True)

# # #     # Info row: poster + metadata
# # #     col_poster, col_info = st.columns([1, 3], gap="large")
# # #     with col_poster:
# # #         if details.get("poster_url"):
# # #             st.markdown(f"""
# # #             <div class="detail-poster">
# # #                 <img src="{details['poster_url']}" />
# # #             </div>""", unsafe_allow_html=True)

# # #     with col_info:
# # #         year = (details.get("release_date") or "")[:4]
# # #         st.markdown(f'<div class="detail-title">{details.get("title","")}</div>', unsafe_allow_html=True)
# # #         genres_str = " · ".join(g["name"] for g in details.get("genres", []))
# # #         st.markdown(f'<p style="color:#9090B0;font-size:13px;margin-bottom:16px;">{genres_str}</p>', unsafe_allow_html=True)
# # #         st.markdown(f'<p class="detail-overview">{details.get("overview","No overview available.")}</p>', unsafe_allow_html=True)

# # #         mc1, mc2 = st.columns(2)
# # #         with mc1:
# # #             st.markdown(f"""
# # #             <div class="detail-stat-card">
# # #                 <div class="detail-stat-val">{year}</div>
# # #                 <div class="detail-stat-label">Release Year</div>
# # #             </div>""", unsafe_allow_html=True)
# # #         with mc2:
# # #             release = details.get("release_date", "Unknown")
# # #             st.markdown(f"""
# # #             <div class="detail-stat-card">
# # #                 <div class="detail-stat-val" style="font-size:16px;">{release}</div>
# # #                 <div class="detail-stat-label">Release Date</div>
# # #             </div>""", unsafe_allow_html=True)

# # #     # Recommendations
# # #     if bundle:
# # #         tfidf_recs = bundle.get("tfidf_recommendations", [])
# # #         genre_recs = bundle.get("genre_recommendations", [])

# # #         if tfidf_recs:
# # #             section_header("Because You Liked This", "TF-IDF Content Matching")
# # #             render_movie_grid(tfidf_recs, cols=6, show_score=True)

# # #         if genre_recs:
# # #             section_header("More in This Genre", "TMDB Discovery")
# # #             render_movie_grid(genre_recs, cols=6)


# # # def page_trending():
# # #     st.markdown('<h1 class="page-title">Trending Today</h1>', unsafe_allow_html=True)
# # #     st.markdown('<p class="page-subtitle">What the world is watching right now</p>', unsafe_allow_html=True)

# # #     with st.spinner("Loading trending films..."):
# # #         movies = get_home_feed("trending", limit=24)

# # #     if movies:
# # #         render_movie_grid(movies, cols=6)


# # # def page_top_rated():
# # #     st.markdown('<h1 class="page-title">Top Rated</h1>', unsafe_allow_html=True)
# # #     st.markdown('<p class="page-subtitle">The all-time greats, as rated by audiences worldwide</p>', unsafe_allow_html=True)

# # #     with st.spinner("Loading top rated films..."):
# # #         movies = get_home_feed("top_rated", limit=24)

# # #     if movies:
# # #         render_movie_grid(movies, cols=6)


# # # # ─────────────────────────────────────────────
# # # # SIDEBAR
# # # # ─────────────────────────────────────────────
# # # with st.sidebar:
# # #     st.markdown("""
# # #     <div class="nav-brand">
# # #         <h1>CineMatch</h1>
# # #         <p>Film Discovery Engine</p>
# # #     </div>""", unsafe_allow_html=True)

# # #     # Status indicator
# # #     if health_check():
# # #         st.markdown('<p style="padding:8px 20px;font-size:11px;color:#4CAF50;">● API Connected</p>', unsafe_allow_html=True)
# # #     else:
# # #         st.markdown('<p style="padding:8px 20px;font-size:11px;color:#E53935;">● API Offline</p>', unsafe_allow_html=True)

# # #     nav = st.radio(
# # #         "Navigation",
# # #         options=["🏠  Home", "🔍  Search", "🔥  Trending", "⭐  Top Rated", "🎬  Details"],
# # #         key="nav",
# # #         label_visibility="hidden",
# # #     )

# # #     # Sync nav with page state
# # #     page_map = {
# # #         "🏠  Home": "Home",
# # #         "🔍  Search": "Search",
# # #         "🔥  Trending": "Trending",
# # #         "⭐  Top Rated": "Top Rated",
# # #         "🎬  Details": "Details",
# # #     }

# # #     selected_page = page_map[nav]
# # #     if st.session_state.get("page") and st.session_state["page"] != selected_page:
# # #         # Programmatic navigation (card click) overrides sidebar
# # #         pass

# # #     st.markdown("<br>" * 2, unsafe_allow_html=True)
# # #     st.markdown('<p style="padding:8px 20px;font-size:10px;color:#3A3A5A;letter-spacing:0.5px;">POWERED BY TMDB & TF-IDF</p>', unsafe_allow_html=True)


# # # # ─────────────────────────────────────────────
# # # # ROUTER
# # # # ─────────────────────────────────────────────
# # # # Handle programmatic navigation from card clicks
# # # prog_page = st.session_state.get("page")
# # # if prog_page:
# # #     current_page = prog_page
# # #     st.session_state.pop("page")  # consume it
# # # else:
# # #     current_page = page_map[nav]

# # # if current_page == "Home":
# # #     page_home()
# # # elif current_page == "Search":
# # #     page_search()
# # # elif current_page == "Trending":
# # #     page_trending()
# # # elif current_page == "Top Rated":
# # #     page_top_rated()
# # # elif current_page == "Details":
# # #     page_details()
# # import streamlit as st
# # import requests
# # from typing import Optional, List, Dict, Any

# # # ─────────────────────────────────────────────
# # # CONFIG
# # # ─────────────────────────────────────────────
# # API_BASE = "http://localhost:8000"

# # st.set_page_config(
# #     page_title="CineMatch",
# #     page_icon="🎬",
# #     layout="wide",
# #     initial_sidebar_state="expanded",
# # )

# # # ─────────────────────────────────────────────
# # # GLOBAL CSS
# # # ─────────────────────────────────────────────
# # st.markdown("""
# # <style>
# # @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700;900&display=swap');

# # *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

# # html, body, [data-testid="stApp"] {
# #     background: #0A0A0F !important;
# #     color: #E8E8F0 !important;
# #     font-family: 'Inter', sans-serif;
# # }

# # /* Hide Streamlit chrome */
# # #MainMenu, footer, header, [data-testid="stToolbar"],
# # [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

# # /* ── Sidebar ── */
# # [data-testid="stSidebar"] {
# #     background: #0D0D18 !important;
# #     border-right: 1px solid #1E1E2E !important;
# #     padding-top: 0 !important;
# # }
# # [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

# # .nav-brand {
# #     padding: 28px 20px 24px;
# #     border-bottom: 1px solid #1E1E2E;
# #     margin-bottom: 12px;
# # }
# # .nav-brand h1 {
# #     font-family: 'Playfair Display', serif;
# #     font-size: 26px;
# #     font-weight: 900;
# #     background: linear-gradient(135deg, #F5A623, #FF6B35);
# #     -webkit-background-clip: text;
# #     -webkit-text-fill-color: transparent;
# #     background-clip: text;
# #     letter-spacing: -0.5px;
# # }
# # .nav-brand p {
# #     color: #6B6B8A;
# #     font-size: 11px;
# #     letter-spacing: 1.5px;
# #     text-transform: uppercase;
# #     margin-top: 2px;
# # }

# # [data-testid="stSidebar"] .stRadio > label { display: none; }
# # [data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
# # [data-testid="stSidebar"] .stRadio > div > label {
# #     display: flex !important;
# #     align-items: center !important;
# #     gap: 10px !important;
# #     padding: 10px 20px !important;
# #     border-radius: 8px !important;
# #     cursor: pointer !important;
# #     font-size: 14px !important;
# #     font-weight: 500 !important;
# #     color: #9090B0 !important;
# #     transition: all 0.15s ease !important;
# #     background: transparent !important;
# #     border: none !important;
# #     margin: 1px 8px !important;
# #     width: calc(100% - 16px) !important;
# # }
# # [data-testid="stSidebar"] .stRadio > div > label:hover {
# #     background: #1E1E2E !important;
# #     color: #E8E8F0 !important;
# # }
# # [data-testid="stSidebar"] .stRadio [aria-checked="true"] {
# #     background: linear-gradient(135deg, rgba(245,166,35,0.15), rgba(255,107,53,0.08)) !important;
# #     color: #F5A623 !important;
# #     border-left: 2px solid #F5A623 !important;
# #     padding-left: 18px !important;
# # }

# # /* ── Main area ── */
# # section[data-testid="stMain"] .block-container {
# #     padding: 32px 40px !important;
# #     max-width: 1400px !important;
# # }

# # /* ── Movie grid card ── */
# # .cm-card {
# #     background: #141420;
# #     border-radius: 12px;
# #     overflow: hidden;
# #     border: 1px solid #1E1E2E;
# #     transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
# #     display: flex;
# #     flex-direction: column;
# #     height: 100%;
# # }
# # .cm-card:hover {
# #     transform: translateY(-4px);
# #     box-shadow: 0 12px 40px rgba(245,166,35,0.15);
# #     border-color: rgba(245,166,35,0.35);
# # }
# # /* The image rendered by st.image sits inside a figure; fix its sizing */
# # [data-testid="stImage"] {
# #     margin: 0 !important;
# #     padding: 0 !important;
# #     display: block !important;
# #     line-height: 0 !important;
# # }
# # [data-testid="stImage"] img {
# #     width: 100% !important;
# #     aspect-ratio: 2/3 !important;
# #     object-fit: cover !important;
# #     border-radius: 12px 12px 0 0 !important;
# #     display: block !important;
# # }
# # /* No-image placeholder */
# # .cm-no-img {
# #     width: 100%;
# #     aspect-ratio: 2/3;
# #     background: linear-gradient(145deg, #1E1E2E, #0D0D18);
# #     display: flex;
# #     align-items: center;
# #     justify-content: center;
# #     font-size: 40px;
# #     border-radius: 12px 12px 0 0;
# # }
# # .cm-body { padding: 10px 12px 12px; flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
# # .cm-title {
# #     font-size: 12px;
# #     font-weight: 600;
# #     color: #E8E8F0;
# #     line-height: 1.35;
# #     margin-bottom: 6px;
# #     display: -webkit-box;
# #     -webkit-line-clamp: 2;
# #     -webkit-box-orient: vertical;
# #     overflow: hidden;
# # }
# # .cm-meta { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
# # .cm-year { font-size: 11px; color: #6B6B8A; }
# # .cm-rating { font-size: 11px; font-weight: 600; color: #F5A623; }
# # .cm-score {
# #     display: inline-block;
# #     background: rgba(245,166,35,0.15);
# #     border: 1px solid rgba(245,166,35,0.3);
# #     color: #F5A623;
# #     font-size: 10px;
# #     font-weight: 700;
# #     padding: 2px 6px;
# #     border-radius: 20px;
# # }

# # /* ── Details button inside card ── */
# # .stButton > button {
# #     background: linear-gradient(135deg, #F5A623, #FF6B35) !important;
# #     color: #0A0A0F !important;
# #     border: none !important;
# #     border-radius: 0 0 10px 10px !important;
# #     font-weight: 700 !important;
# #     font-size: 12px !important;
# #     padding: 8px 0 !important;
# #     width: 100% !important;
# #     transition: opacity 0.2s ease !important;
# #     font-family: 'Inter', sans-serif !important;
# #     letter-spacing: 0.3px !important;
# # }
# # .stButton > button:hover { opacity: 0.88 !important; }

# # /* ── Hero ── */
# # .hero {
# #     position: relative;
# #     border-radius: 16px;
# #     overflow: hidden;
# #     margin-bottom: 36px;
# # }
# # .hero-img {
# #     width: 100%;
# #     height: 420px;
# #     object-fit: cover;
# #     display: block;
# # }
# # .hero-overlay {
# #     position: absolute;
# #     inset: 0;
# #     background: linear-gradient(90deg,
# #         rgba(10,10,15,0.97) 0%,
# #         rgba(10,10,15,0.82) 42%,
# #         rgba(10,10,15,0.25) 70%,
# #         transparent 100%);
# #     display: flex;
# #     align-items: flex-end;
# #     padding: 40px;
# # }
# # .hero-content { max-width: 500px; }
# # .hero-genres { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
# # .genre-pill {
# #     background: rgba(245,166,35,0.15);
# #     border: 1px solid rgba(245,166,35,0.4);
# #     color: #F5A623;
# #     font-size: 10px;
# #     font-weight: 700;
# #     padding: 3px 10px;
# #     border-radius: 20px;
# #     text-transform: uppercase;
# #     letter-spacing: 0.8px;
# # }
# # .hero-title {
# #     font-family: 'Playfair Display', serif;
# #     font-size: 42px;
# #     font-weight: 900;
# #     color: #FFFFFF;
# #     line-height: 1.1;
# #     margin-bottom: 10px;
# #     letter-spacing: -1px;
# # }
# # .hero-overview {
# #     font-size: 13px;
# #     color: #B0B0C8;
# #     line-height: 1.6;
# #     margin-bottom: 18px;
# #     display: -webkit-box;
# #     -webkit-line-clamp: 3;
# #     -webkit-box-orient: vertical;
# #     overflow: hidden;
# # }
# # .hero-stats { display: flex; align-items: center; gap: 20px; }
# # .hero-stat-label { font-size: 10px; color: #6B6B8A; letter-spacing: 1px; text-transform: uppercase; }
# # .hero-stat-value { font-size: 20px; font-weight: 700; color: #F5A623; }

# # /* ── Section header ── */
# # .section-header {
# #     display: flex;
# #     align-items: center;
# #     gap: 16px;
# #     margin-bottom: 18px;
# #     margin-top: 38px;
# # }
# # .section-header h2 {
# #     font-family: 'Playfair Display', serif;
# #     font-size: 20px;
# #     font-weight: 700;
# #     color: #E8E8F0;
# #     white-space: nowrap;
# # }
# # .section-div {
# #     flex: 1;
# #     height: 1px;
# #     background: linear-gradient(90deg, #2A2A40, transparent);
# # }
# # .section-label {
# #     font-size: 10px;
# #     color: #6B6B8A;
# #     letter-spacing: 1.2px;
# #     text-transform: uppercase;
# #     white-space: nowrap;
# # }

# # /* ── Page title ── */
# # .page-title {
# #     font-family: 'Playfair Display', serif;
# #     font-size: 30px;
# #     font-weight: 900;
# #     color: #FFFFFF;
# #     margin-bottom: 4px;
# #     letter-spacing: -0.5px;
# # }
# # .page-subtitle { font-size: 13px; color: #6B6B8A; margin-bottom: 28px; }

# # /* ── Detail page ── */
# # .detail-poster img {
# #     width: 100%;
# #     border-radius: 12px;
# #     box-shadow: 0 20px 60px rgba(0,0,0,0.5);
# #     display: block;
# # }
# # .detail-title {
# #     font-family: 'Playfair Display', serif;
# #     font-size: 34px;
# #     font-weight: 900;
# #     color: #FFFFFF;
# #     line-height: 1.1;
# #     margin-bottom: 10px;
# #     letter-spacing: -0.8px;
# # }
# # .detail-overview { font-size: 14px; color: #B0B0C8; line-height: 1.7; margin-bottom: 22px; }
# # .detail-stat-card {
# #     background: #141420;
# #     border: 1px solid #1E1E2E;
# #     border-radius: 10px;
# #     padding: 14px 18px;
# #     text-align: center;
# # }
# # .detail-stat-val { font-size: 22px; font-weight: 700; color: #F5A623; }
# # .detail-stat-label { font-size: 10px; color: #6B6B8A; text-transform: uppercase; letter-spacing: 1px; margin-top: 3px; }

# # /* ── Empty state ── */
# # .empty-state {
# #     text-align: center;
# #     padding: 70px 40px;
# #     color: #4A4A6A;
# # }
# # .empty-state .ei { font-size: 44px; margin-bottom: 14px; }
# # .empty-state h3 { font-size: 17px; color: #6B6B8A; margin-bottom: 6px; }
# # .empty-state p { font-size: 13px; }

# # /* ── Input ── */
# # [data-testid="stTextInput"] > div > div > input {
# #     background: #141420 !important;
# #     border: 1px solid #2A2A40 !important;
# #     border-radius: 10px !important;
# #     color: #E8E8F0 !important;
# #     padding: 14px 18px !important;
# #     font-size: 15px !important;
# #     font-family: 'Inter', sans-serif !important;
# # }
# # [data-testid="stTextInput"] > div > div > input:focus {
# #     border-color: #F5A623 !important;
# #     box-shadow: 0 0 0 3px rgba(245,166,35,0.1) !important;
# # }
# # [data-testid="stTextInput"] > div > div > input::placeholder { color: #4A4A6A !important; }

# # /* ── Selectbox ── */
# # [data-testid="stSelectbox"] > div > div {
# #     background: #141420 !important;
# #     border: 1px solid #2A2A40 !important;
# #     border-radius: 10px !important;
# #     color: #E8E8F0 !important;
# # }

# # /* ── Tabs ── */
# # [data-testid="stTabs"] [role="tablist"] {
# #     border-bottom: 1px solid #1E1E2E !important;
# #     background: transparent !important;
# # }
# # [data-testid="stTabs"] [role="tab"] {
# #     color: #6B6B8A !important;
# #     font-size: 13px !important;
# #     font-weight: 500 !important;
# #     padding: 10px 20px !important;
# #     border: none !important;
# #     background: transparent !important;
# #     border-bottom: 2px solid transparent !important;
# # }
# # [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
# #     color: #F5A623 !important;
# #     border-bottom-color: #F5A623 !important;
# # }

# # /* Scrollbar */
# # ::-webkit-scrollbar { width: 6px; height: 6px; }
# # ::-webkit-scrollbar-track { background: #0A0A0F; }
# # ::-webkit-scrollbar-thumb { background: #2A2A40; border-radius: 3px; }
# # ::-webkit-scrollbar-thumb:hover { background: #F5A623; }
# # </style>
# # """, unsafe_allow_html=True)


# # # ─────────────────────────────────────────────
# # # API HELPERS
# # # ─────────────────────────────────────────────
# # def api_get(path: str, params: Dict = None) -> Optional[Any]:
# #     try:
# #         r = requests.get(f"{API_BASE}{path}", params=params or {}, timeout=20)
# #         r.raise_for_status()
# #         return r.json()
# #     except requests.exceptions.ConnectionError:
# #         st.error("⚠️ Cannot reach the backend. Make sure FastAPI is running on localhost:8000.")
# #         return None
# #     except requests.exceptions.HTTPError as e:
# #         st.error(f"API error {e.response.status_code}: {e.response.text[:200]}")
# #         return None
# #     except Exception as e:
# #         st.error(f"Unexpected error: {e}")
# #         return None


# # @st.cache_data(ttl=300)
# # def get_home_feed(category: str, limit: int = 24):
# #     return api_get("/home", {"category": category, "limit": limit})

# # @st.cache_data(ttl=60)
# # def search_movies(query: str, page: int = 1):
# #     return api_get("/tmdb/search", {"query": query, "page": page})

# # @st.cache_data(ttl=300)
# # def get_search_bundle(query: str, tfidf_top_n: int = 12, genre_limit: int = 12):
# #     return api_get("/movie/search", {"query": query, "tfidf_top_n": tfidf_top_n, "genre_limit": genre_limit})

# # @st.cache_data(ttl=300)
# # def get_movie_details(tmdb_id: int):
# #     return api_get(f"/movie/id/{tmdb_id}")

# # def health_check() -> bool:
# #     try:
# #         r = requests.get(f"{API_BASE}/health", timeout=5)
# #         return r.status_code == 200
# #     except Exception:
# #         return False


# # # ─────────────────────────────────────────────
# # # NORMALISE movie dicts from both API shapes
# # # ─────────────────────────────────────────────
# # def normalise(movie: dict) -> dict:
# #     """
# #     Accepts both a TMDBMovieCard dict and a TFIDFRecItem dict
# #     (which has a nested 'tmdb' key) and returns a flat dict.
# #     """
# #     if "tmdb" in movie and isinstance(movie["tmdb"], dict):
# #         tmdb = movie["tmdb"]
# #         return {
# #             "title":        movie.get("title") or tmdb.get("title", "Unknown"),
# #             "poster_url":   tmdb.get("poster_url"),
# #             "release_date": tmdb.get("release_date"),
# #             "vote_average": tmdb.get("vote_average"),
# #             "tmdb_id":      tmdb.get("tmdb_id"),
# #             "score":        movie.get("score"),
# #         }
# #     return {
# #         "title":        movie.get("title", "Unknown"),
# #         "poster_url":   movie.get("poster_url"),
# #         "release_date": movie.get("release_date"),
# #         "vote_average": movie.get("vote_average"),
# #         "tmdb_id":      movie.get("tmdb_id"),
# #         "score":        movie.get("score"),
# #     }


# # # ─────────────────────────────────────────────
# # # COMPONENT: Render a row of movie cards
# # # Uses st.columns + st.image so Streamlit handles
# # # the image element natively (no broken HTML).
# # # ─────────────────────────────────────────────
# # PLACEHOLDER = "https://via.placeholder.com/300x450/141420/6B6B8A?text=No+Image"

# # def render_movie_grid(movies: List[Dict], cols: int = 6, show_score: bool = False):
# #     if not movies:
# #         st.markdown("""
# #         <div class="empty-state">
# #             <div class="ei">🎬</div>
# #             <h3>No movies found</h3>
# #             <p>Try a different search or category.</p>
# #         </div>""", unsafe_allow_html=True)
# #         return

# #     flat = [normalise(m) for m in movies]

# #     # Chunk into rows of `cols`
# #     for row_start in range(0, len(flat), cols):
# #         row = flat[row_start : row_start + cols]
# #         columns = st.columns(cols, gap="small")

# #         for col_idx, movie in enumerate(row):
# #             with columns[col_idx]:
# #                 title       = movie["title"]
# #                 poster_url  = movie["poster_url"] or PLACEHOLDER
# #                 year        = (movie["release_date"] or "")[:4] or "—"
# #                 rating      = movie["vote_average"]
# #                 score       = movie["score"]
# #                 tmdb_id     = movie["tmdb_id"]

# #                 # Card wrapper top
# #                 st.markdown('<div class="cm-card">', unsafe_allow_html=True)

# #                 # Poster via st.image (Streamlit renders this cleanly)
# #                 st.image(poster_url, use_container_width=True)

# #                 # Card body: title + meta as one safe HTML block
# #                 rating_str = f"★ {rating:.1f}" if rating else "—"
# #                 score_html = (
# #                     f'<span class="cm-score">{score:.2f}</span>'
# #                     if show_score and score is not None else ""
# #                 )
# #                 st.markdown(f"""
# #                 <div class="cm-body">
# #                     <div class="cm-title">{title}</div>
# #                     <div class="cm-meta">
# #                         <span class="cm-year">{year}</span>
# #                         <span class="cm-rating">{rating_str}</span>
# #                         {score_html}
# #                     </div>
# #                 </div>""", unsafe_allow_html=True)

# #                 # Details button
# #                 if tmdb_id:
# #                     if st.button("Details", key=f"btn_{tmdb_id}_{row_start}_{col_idx}"):
# #                         st.session_state["selected_tmdb_id"] = int(tmdb_id)
# #                         st.session_state["selected_title"]   = title
# #                         st.session_state["goto_page"]        = "Details"
# #                         st.rerun()

# #                 st.markdown('</div>', unsafe_allow_html=True)


# # # ─────────────────────────────────────────────
# # # COMPONENT: Section header
# # # ─────────────────────────────────────────────
# # def section_header(title: str, label: str = ""):
# #     label_html = f'<span class="section-label">{label}</span>' if label else ""
# #     st.markdown(f"""
# #     <div class="section-header">
# #         <h2>{title}</h2>
# #         <div class="section-div"></div>
# #         {label_html}
# #     </div>""", unsafe_allow_html=True)


# # # ─────────────────────────────────────────────
# # # COMPONENT: Hero banner
# # # ─────────────────────────────────────────────
# # def render_hero(backdrop_url: str, title: str, overview: str,
# #                 genres: List[Dict], year: str, rating: Optional[float] = None,
# #                 height: int = 420):
# #     genres_html = "".join(
# #         f'<span class="genre-pill">{g["name"]}</span>'
# #         for g in (genres or [])[:4]
# #     )
# #     rating_html = ""
# #     if rating:
# #         rating_html = f"""
# #         <div class="hero-stat">
# #             <div class="hero-stat-label">Rating</div>
# #             <div class="hero-stat-value">★ {rating:.1f}</div>
# #         </div>"""

# #     overview_safe = (overview or "")[:400]
# #     st.markdown(f"""
# #     <div class="hero">
# #         <img class="hero-img" src="{backdrop_url}" style="height:{height}px;" />
# #         <div class="hero-overlay">
# #             <div class="hero-content">
# #                 <div class="hero-genres">{genres_html}</div>
# #                 <div class="hero-title">{title}</div>
# #                 <div class="hero-overview">{overview_safe}</div>
# #                 <div class="hero-stats">
# #                     <div class="hero-stat">
# #                         <div class="hero-stat-label">Year</div>
# #                         <div class="hero-stat-value">{year or "—"}</div>
# #                     </div>
# #                     {rating_html}
# #                 </div>
# #             </div>
# #         </div>
# #     </div>""", unsafe_allow_html=True)


# # # ─────────────────────────────────────────────
# # # PAGES
# # # ─────────────────────────────────────────────
# # def page_home():
# #     cat_map = {
# #         "🔥 Trending":      "trending",
# #         "⭐ Top Rated":     "top_rated",
# #         "🎬 Now Playing":   "now_playing",
# #         "📅 Upcoming":      "upcoming",
# #         "🍿 Popular":       "popular",
# #     }
# #     col_title, col_select = st.columns([3, 1])
# #     with col_title:
# #         st.markdown('<h1 class="page-title">Discover Films</h1>', unsafe_allow_html=True)
# #         st.markdown('<p class="page-subtitle">Find your next watch from the world\'s best movies</p>', unsafe_allow_html=True)
# #     with col_select:
# #         cat_label = st.selectbox("", list(cat_map.keys()), label_visibility="hidden")

# #     category = cat_map[cat_label]
# #     with st.spinner("Loading movies…"):
# #         movies = get_home_feed(category, limit=24)
# #     if not movies:
# #         return

# #     # Hero with the first result
# #     hero = movies[0]
# #     if hero.get("poster_url"):
# #         backdrop = hero["poster_url"].replace("/w500/", "/w1280/")
# #         year = (hero.get("release_date") or "")[:4]
# #         render_hero(
# #             backdrop_url=backdrop,
# #             title=hero.get("title", ""),
# #             overview="",
# #             genres=[],
# #             year=year,
# #             rating=hero.get("vote_average"),
# #             height=380,
# #         )

# #     section_header(f"{cat_label.split(' ', 1)[1]} Movies", f"{len(movies)} films")
# #     render_movie_grid(movies[1:], cols=6)


# # def page_search():
# #     st.markdown('<h1 class="page-title">Search & Discover</h1>', unsafe_allow_html=True)
# #     st.markdown('<p class="page-subtitle">Search for any film to get TF-IDF and genre-based recommendations</p>', unsafe_allow_html=True)

# #     col_input, col_btn = st.columns([5, 1])
# #     with col_input:
# #         query = st.text_input("", placeholder="e.g. The Dark Knight, Inception, Parasite…",
# #                               label_visibility="hidden", key="search_input")
# #     with col_btn:
# #         st.markdown("<br>", unsafe_allow_html=True)
# #         do_search = st.button("Search", use_container_width=True)

# #     if query and (do_search or st.session_state.get("last_search") == query):
# #         st.session_state["last_search"] = query

# #         # ── TMDB search results grid ──
# #         section_header("Search Results", "TMDB")
# #         with st.spinner("Searching TMDB…"):
# #             raw = search_movies(query)
# #         if raw and raw.get("results"):
# #             cards = []
# #             for m in raw["results"][:12]:
# #                 cards.append({
# #                     "title":        m.get("title", ""),
# #                     "poster_url":   f"https://image.tmdb.org/t/p/w500{m['poster_path']}"
# #                                     if m.get("poster_path") else None,
# #                     "release_date": m.get("release_date"),
# #                     "vote_average": m.get("vote_average"),
# #                     "tmdb_id":      m.get("id"),
# #                 })
# #             render_movie_grid(cards, cols=6)

# #         # ── Recommendation bundle ──
# #         st.markdown("<br>", unsafe_allow_html=True)
# #         section_header("AI Recommendations", "TF-IDF + Genre")
# #         with st.spinner("Fetching recommendations…"):
# #             bundle = get_search_bundle(query)

# #         if bundle:
# #             details     = bundle.get("movie_details", {})
# #             tfidf_recs  = bundle.get("tfidf_recommendations", [])
# #             genre_recs  = bundle.get("genre_recommendations", [])

# #             if details.get("backdrop_url"):
# #                 render_hero(
# #                     backdrop_url=details["backdrop_url"],
# #                     title=details.get("title", ""),
# #                     overview=details.get("overview", ""),
# #                     genres=details.get("genres", []),
# #                     year=(details.get("release_date") or "")[:4],
# #                     height=280,
# #                 )

# #             tab1, tab2 = st.tabs(["🧠  Content-Based (TF-IDF)", "🎭  Same Genre"])

# #             with tab1:
# #                 if tfidf_recs:
# #                     render_movie_grid(tfidf_recs, cols=6, show_score=True)
# #                 else:
# #                     st.markdown("""<div class="empty-state">
# #                         <div class="ei">🤔</div>
# #                         <h3>No TF-IDF matches</h3>
# #                         <p>This title may not be in the local dataset.</p>
# #                     </div>""", unsafe_allow_html=True)

# #             with tab2:
# #                 if genre_recs:
# #                     render_movie_grid(genre_recs, cols=6)
# #                 else:
# #                     st.markdown("""<div class="empty-state">
# #                         <div class="ei">🎭</div>
# #                         <h3>No genre recommendations</h3>
# #                         <p>Could not find genre data for this film.</p>
# #                     </div>""", unsafe_allow_html=True)
# #         else:
# #             st.markdown("""<div class="empty-state">
# #                 <div class="ei">⚠️</div>
# #                 <h3>Recommendations unavailable</h3>
# #                 <p>The backend may be busy — try again in a moment.</p>
# #             </div>""", unsafe_allow_html=True)
# #     else:
# #         st.markdown("""
# #         <div class="empty-state" style="margin-top:60px;">
# #             <div class="ei">🔍</div>
# #             <h3>Search for a film to get started</h3>
# #             <p>Type a movie title above and press Search.</p>
# #         </div>""", unsafe_allow_html=True)


# # def page_details():
# #     tmdb_id       = st.session_state.get("selected_tmdb_id")
# #     selected_title = st.session_state.get("selected_title", "")

# #     if not tmdb_id:
# #         st.markdown("""<div class="empty-state" style="margin-top:80px;">
# #             <div class="ei">🎬</div>
# #             <h3>No film selected</h3>
# #             <p>Click "Details" on any movie card to open this page.</p>
# #         </div>""", unsafe_allow_html=True)
# #         return

# #     with st.spinner("Loading film…"):
# #         details = get_movie_details(tmdb_id)
# #         bundle  = get_search_bundle(selected_title) if selected_title else None

# #     if not details:
# #         st.error("Could not load movie details.")
# #         return

# #     # Full-bleed hero
# #     if details.get("backdrop_url"):
# #         render_hero(
# #             backdrop_url=details["backdrop_url"],
# #             title=details.get("title", ""),
# #             overview=details.get("overview", ""),
# #             genres=details.get("genres", []),
# #             year=(details.get("release_date") or "")[:4],
# #             height=460,
# #         )

# #     # Poster + info
# #     col_poster, col_info = st.columns([1, 3], gap="large")
# #     with col_poster:
# #         if details.get("poster_url"):
# #             st.markdown('<div class="detail-poster">', unsafe_allow_html=True)
# #             st.image(details["poster_url"], use_container_width=True)
# #             st.markdown('</div>', unsafe_allow_html=True)

# #     with col_info:
# #         year       = (details.get("release_date") or "")[:4]
# #         genres_str = " · ".join(g["name"] for g in details.get("genres", []))

# #         st.markdown(f'<div class="detail-title">{details.get("title","")}</div>', unsafe_allow_html=True)
# #         st.markdown(f'<p style="color:#9090B0;font-size:13px;margin-bottom:14px;">{genres_str}</p>',
# #                     unsafe_allow_html=True)
# #         st.markdown(f'<p class="detail-overview">{details.get("overview","No overview available.")}</p>',
# #                     unsafe_allow_html=True)

# #         sc1, sc2 = st.columns(2)
# #         with sc1:
# #             st.markdown(f"""
# #             <div class="detail-stat-card">
# #                 <div class="detail-stat-val">{year}</div>
# #                 <div class="detail-stat-label">Release Year</div>
# #             </div>""", unsafe_allow_html=True)
# #         with sc2:
# #             rd = details.get("release_date", "Unknown")
# #             st.markdown(f"""
# #             <div class="detail-stat-card">
# #                 <div class="detail-stat-val" style="font-size:17px;">{rd}</div>
# #                 <div class="detail-stat-label">Release Date</div>
# #             </div>""", unsafe_allow_html=True)

# #     # Recommendations
# #     if bundle:
# #         tfidf_recs = bundle.get("tfidf_recommendations", [])
# #         genre_recs = bundle.get("genre_recommendations", [])
# #         if tfidf_recs:
# #             section_header("Because You Liked This", "TF-IDF Content Matching")
# #             render_movie_grid(tfidf_recs, cols=6, show_score=True)
# #         if genre_recs:
# #             section_header("More in This Genre", "TMDB Discovery")
# #             render_movie_grid(genre_recs, cols=6)


# # def page_trending():
# #     st.markdown('<h1 class="page-title">Trending Today</h1>', unsafe_allow_html=True)
# #     st.markdown('<p class="page-subtitle">What the world is watching right now</p>', unsafe_allow_html=True)
# #     with st.spinner("Loading…"):
# #         movies = get_home_feed("trending", limit=24)
# #     if movies:
# #         render_movie_grid(movies, cols=6)


# # def page_top_rated():
# #     st.markdown('<h1 class="page-title">Top Rated</h1>', unsafe_allow_html=True)
# #     st.markdown('<p class="page-subtitle">The all-time greats, as rated by audiences worldwide</p>', unsafe_allow_html=True)
# #     with st.spinner("Loading…"):
# #         movies = get_home_feed("top_rated", limit=24)
# #     if movies:
# #         render_movie_grid(movies, cols=6)


# # # ─────────────────────────────────────────────
# # # SIDEBAR
# # # ─────────────────────────────────────────────
# # page_map = {
# #     "🏠  Home":      "Home",
# #     "🔍  Search":    "Search",
# #     "🔥  Trending":  "Trending",
# #     "⭐  Top Rated": "Top Rated",
# #     "🎬  Details":   "Details",
# # }

# # with st.sidebar:
# #     st.markdown("""
# #     <div class="nav-brand">
# #         <h1>CineMatch</h1>
# #         <p>Film Discovery Engine</p>
# #     </div>""", unsafe_allow_html=True)

# #     api_ok = health_check()
# #     status_color = "#4CAF50" if api_ok else "#E53935"
# #     status_text  = "API Connected" if api_ok else "API Offline"
# #     st.markdown(
# #         f'<p style="padding:6px 20px 12px;font-size:11px;color:{status_color};">● {status_text}</p>',
# #         unsafe_allow_html=True
# #     )

# #     nav = st.radio("Navigation", list(page_map.keys()),
# #                    key="nav", label_visibility="hidden")

# #     st.markdown("<br>" * 3, unsafe_allow_html=True)
# #     st.markdown(
# #         '<p style="padding:8px 20px;font-size:10px;color:#3A3A5A;letter-spacing:0.5px;">POWERED BY TMDB & TF-IDF</p>',
# #         unsafe_allow_html=True
# #     )


# # # ─────────────────────────────────────────────
# # # ROUTER — programmatic nav wins over sidebar
# # # ─────────────────────────────────────────────
# # goto = st.session_state.pop("goto_page", None)
# # current_page = goto if goto else page_map[nav]

# # if current_page == "Home":
# #     page_home()
# # elif current_page == "Search":
# #     page_search()
# # elif current_page == "Trending":
# #     page_trending()
# # elif current_page == "Top Rated":
# #     page_top_rated()
# # elif current_page == "Details":
# #     page_details()
# import streamlit as st
# import requests
# from typing import Optional, List, Dict, Any

# # ─────────────────────────────────────────────
# # CONFIG
# # ─────────────────────────────────────────────
# API_BASE = "http://localhost:8000"

# st.set_page_config(
#     page_title="CineMatch",
#     page_icon="🎬",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ─────────────────────────────────────────────
# # GLOBAL CSS
# # ─────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700;900&display=swap');

# *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

# html, body, [data-testid="stApp"] {
#     background: #0A0A0F !important;
#     color: #E8E8F0 !important;
#     font-family: 'Inter', sans-serif;
# }

# #MainMenu, footer, header, [data-testid="stToolbar"],
# [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

# /* ── Sidebar ── */
# [data-testid="stSidebar"] {
#     background: #0D0D18 !important;
#     border-right: 1px solid #1E1E2E !important;
#     padding-top: 0 !important;
# }
# [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

# .nav-brand {
#     padding: 28px 20px 24px;
#     border-bottom: 1px solid #1E1E2E;
#     margin-bottom: 12px;
# }
# .nav-brand h1 {
#     font-family: 'Playfair Display', serif;
#     font-size: 26px;
#     font-weight: 900;
#     background: linear-gradient(135deg, #F5A623, #FF6B35);
#     -webkit-background-clip: text;
#     -webkit-text-fill-color: transparent;
#     background-clip: text;
#     letter-spacing: -0.5px;
# }
# .nav-brand p { color: #6B6B8A; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }

# [data-testid="stSidebar"] .stRadio > label { display: none; }
# [data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
# [data-testid="stSidebar"] .stRadio > div > label {
#     display: flex !important; align-items: center !important; gap: 10px !important;
#     padding: 10px 20px !important; border-radius: 8px !important; cursor: pointer !important;
#     font-size: 14px !important; font-weight: 500 !important; color: #9090B0 !important;
#     transition: all 0.15s ease !important; background: transparent !important;
#     border: none !important; margin: 1px 8px !important; width: calc(100% - 16px) !important;
# }
# [data-testid="stSidebar"] .stRadio > div > label:hover {
#     background: #1E1E2E !important; color: #E8E8F0 !important;
# }
# [data-testid="stSidebar"] .stRadio [aria-checked="true"] {
#     background: linear-gradient(135deg, rgba(245,166,35,0.15), rgba(255,107,53,0.08)) !important;
#     color: #F5A623 !important; border-left: 2px solid #F5A623 !important; padding-left: 18px !important;
# }

# section[data-testid="stMain"] .block-container {
#     padding: 32px 40px !important;
#     max-width: 1400px !important;
# }

# /* ── Hero ── */
# .cm-hero {
#     position: relative;
#     border-radius: 16px;
#     overflow: hidden;
#     margin-bottom: 36px;
#     width: 100%;
# }
# .cm-hero-img {
#     width: 100%;
#     object-fit: cover;
#     display: block;
# }
# .cm-hero-overlay {
#     position: absolute;
#     inset: 0;
#     background: linear-gradient(90deg,
#         rgba(10,10,15,0.97) 0%,
#         rgba(10,10,15,0.82) 42%,
#         rgba(10,10,15,0.25) 70%,
#         transparent 100%);
#     display: flex;
#     align-items: flex-end;
#     padding: 40px;
# }
# .cm-hero-inner { max-width: 500px; }
# .cm-genre-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
# .cm-pill {
#     background: rgba(245,166,35,0.15);
#     border: 1px solid rgba(245,166,35,0.4);
#     color: #F5A623;
#     font-size: 10px; font-weight: 700;
#     padding: 3px 10px; border-radius: 20px;
#     text-transform: uppercase; letter-spacing: 0.8px;
# }
# .cm-hero-title {
#     font-family: 'Playfair Display', serif;
#     font-size: 42px; font-weight: 900; color: #FFFFFF;
#     line-height: 1.1; margin-bottom: 10px; letter-spacing: -1px;
# }
# .cm-hero-overview {
#     font-size: 13px; color: #B0B0C8; line-height: 1.6; margin-bottom: 18px;
#     display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
# }
# .cm-hero-stats { display: flex; align-items: center; gap: 24px; }
# .cm-stat-label { font-size: 10px; color: #6B6B8A; letter-spacing: 1px; text-transform: uppercase; }
# .cm-stat-val { font-size: 20px; font-weight: 700; color: #F5A623; }

# /* ── Movie cards ── */
# .cm-card {
#     background: #141420;
#     border-radius: 12px;
#     overflow: hidden;
#     border: 1px solid #1E1E2E;
#     transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
# }
# .cm-card:hover {
#     transform: translateY(-4px);
#     box-shadow: 0 12px 40px rgba(245,166,35,0.15);
#     border-color: rgba(245,166,35,0.35);
# }
# /* Make st.image fill the card cleanly */
# .cm-card [data-testid="stImage"],
# .cm-card [data-testid="stImage"] > img {
#     display: block !important;
#     width: 100% !important;
#     margin: 0 !important;
#     padding: 0 !important;
#     border-radius: 0 !important;
#     line-height: 0 !important;
# }
# .cm-card [data-testid="stImage"] > img {
#     aspect-ratio: 2/3 !important;
#     object-fit: cover !important;
# }
# .cm-card-body { padding: 10px 12px 12px; }
# .cm-card-title {
#     font-size: 12px; font-weight: 600; color: #E8E8F0; line-height: 1.35;
#     margin-bottom: 6px;
#     display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
# }
# .cm-card-meta { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
# .cm-card-year { font-size: 11px; color: #6B6B8A; }
# .cm-card-rating { font-size: 11px; font-weight: 600; color: #F5A623; }
# .cm-score {
#     display: inline-block;
#     background: rgba(245,166,35,0.15); border: 1px solid rgba(245,166,35,0.3);
#     color: #F5A623; font-size: 10px; font-weight: 700;
#     padding: 2px 6px; border-radius: 20px;
# }

# /* ── Details button ── */
# .stButton > button {
#     background: linear-gradient(135deg, #F5A623, #FF6B35) !important;
#     color: #0A0A0F !important; border: none !important;
#     border-radius: 0 0 10px 10px !important;
#     font-weight: 700 !important; font-size: 12px !important;
#     padding: 8px 0 !important; width: 100% !important;
#     transition: opacity 0.2s ease !important;
#     font-family: 'Inter', sans-serif !important; letter-spacing: 0.3px !important;
# }
# .stButton > button:hover { opacity: 0.88 !important; }

# /* ── Section header ── */
# .cm-section {
#     display: flex; align-items: center; gap: 16px;
#     margin-bottom: 18px; margin-top: 38px;
# }
# .cm-section h2 {
#     font-family: 'Playfair Display', serif; font-size: 20px;
#     font-weight: 700; color: #E8E8F0; white-space: nowrap;
# }
# .cm-section-div { flex: 1; height: 1px; background: linear-gradient(90deg, #2A2A40, transparent); }
# .cm-section-lbl { font-size: 10px; color: #6B6B8A; letter-spacing: 1.2px; text-transform: uppercase; white-space: nowrap; }

# /* ── Page title ── */
# .cm-page-title {
#     font-family: 'Playfair Display', serif; font-size: 30px;
#     font-weight: 900; color: #FFFFFF; margin-bottom: 4px; letter-spacing: -0.5px;
# }
# .cm-page-sub { font-size: 13px; color: #6B6B8A; margin-bottom: 28px; }

# /* ── Detail page ── */
# .cm-detail-title {
#     font-family: 'Playfair Display', serif; font-size: 32px;
#     font-weight: 900; color: #FFFFFF; line-height: 1.1; margin-bottom: 10px; letter-spacing: -0.8px;
# }
# .cm-detail-overview { font-size: 14px; color: #B0B0C8; line-height: 1.7; margin-bottom: 22px; }
# .cm-stat-card {
#     background: #141420; border: 1px solid #1E1E2E; border-radius: 10px;
#     padding: 14px 18px; text-align: center;
# }
# .cm-stat-card-val { font-size: 22px; font-weight: 700; color: #F5A623; }
# .cm-stat-card-label { font-size: 10px; color: #6B6B8A; text-transform: uppercase; letter-spacing: 1px; margin-top: 3px; }

# /* ── Empty state ── */
# .cm-empty { text-align: center; padding: 70px 40px; color: #4A4A6A; }
# .cm-empty .ei { font-size: 44px; margin-bottom: 14px; }
# .cm-empty h3 { font-size: 17px; color: #6B6B8A; margin-bottom: 6px; }
# .cm-empty p { font-size: 13px; }

# /* ── Input ── */
# [data-testid="stTextInput"] > div > div > input {
#     background: #141420 !important; border: 1px solid #2A2A40 !important;
#     border-radius: 10px !important; color: #E8E8F0 !important;
#     padding: 14px 18px !important; font-size: 15px !important; font-family: 'Inter', sans-serif !important;
# }
# [data-testid="stTextInput"] > div > div > input:focus {
#     border-color: #F5A623 !important; box-shadow: 0 0 0 3px rgba(245,166,35,0.1) !important;
# }
# [data-testid="stTextInput"] > div > div > input::placeholder { color: #4A4A6A !important; }

# [data-testid="stSelectbox"] > div > div {
#     background: #141420 !important; border: 1px solid #2A2A40 !important;
#     border-radius: 10px !important; color: #E8E8F0 !important;
# }

# /* ── Tabs ── */
# [data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid #1E1E2E !important; background: transparent !important; }
# [data-testid="stTabs"] [role="tab"] {
#     color: #6B6B8A !important; font-size: 13px !important; font-weight: 500 !important;
#     padding: 10px 20px !important; border: none !important; background: transparent !important;
#     border-bottom: 2px solid transparent !important;
# }
# [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #F5A623 !important; border-bottom-color: #F5A623 !important; }

# ::-webkit-scrollbar { width: 6px; height: 6px; }
# ::-webkit-scrollbar-track { background: #0A0A0F; }
# ::-webkit-scrollbar-thumb { background: #2A2A40; border-radius: 3px; }
# ::-webkit-scrollbar-thumb:hover { background: #F5A623; }
# </style>
# """, unsafe_allow_html=True)


# # ─────────────────────────────────────────────
# # API HELPERS
# # ─────────────────────────────────────────────
# def api_get(path: str, params: Dict = None) -> Optional[Any]:
#     try:
#         r = requests.get(f"{API_BASE}{path}", params=params or {}, timeout=20)
#         r.raise_for_status()
#         return r.json()
#     except requests.exceptions.ConnectionError:
#         st.error("⚠️ Cannot reach the backend. Make sure FastAPI is running on localhost:8000.")
#         return None
#     except requests.exceptions.HTTPError as e:
#         st.error(f"API error {e.response.status_code}: {e.response.text[:200]}")
#         return None
#     except Exception as e:
#         st.error(f"Unexpected error: {e}")
#         return None


# @st.cache_data(ttl=300)
# def get_home_feed(category: str, limit: int = 24):
#     return api_get("/home", {"category": category, "limit": limit})

# @st.cache_data(ttl=60)
# def search_movies(query: str, page: int = 1):
#     return api_get("/tmdb/search", {"query": query, "page": page})

# @st.cache_data(ttl=300)
# def get_search_bundle(query: str, tfidf_top_n: int = 12, genre_limit: int = 12):
#     return api_get("/movie/search", {"query": query, "tfidf_top_n": tfidf_top_n, "genre_limit": genre_limit})

# @st.cache_data(ttl=300)
# def get_movie_details(tmdb_id: int):
#     return api_get(f"/movie/id/{tmdb_id}")

# def health_check() -> bool:
#     try:
#         r = requests.get(f"{API_BASE}/health", timeout=5)
#         return r.status_code == 200
#     except Exception:
#         return False


# # ─────────────────────────────────────────────
# # NORMALISE — handle TMDBMovieCard and TFIDFRecItem
# # ─────────────────────────────────────────────
# def normalise(movie: dict) -> dict:
#     if "tmdb" in movie and isinstance(movie["tmdb"], dict):
#         t = movie["tmdb"]
#         return {
#             "title":        movie.get("title") or t.get("title", "Unknown"),
#             "poster_url":   t.get("poster_url"),
#             "release_date": t.get("release_date"),
#             "vote_average": t.get("vote_average"),
#             "tmdb_id":      t.get("tmdb_id"),
#             "score":        movie.get("score"),
#         }
#     return {
#         "title":        movie.get("title", "Unknown"),
#         "poster_url":   movie.get("poster_url"),
#         "release_date": movie.get("release_date"),
#         "vote_average": movie.get("vote_average"),
#         "tmdb_id":      movie.get("tmdb_id"),
#         "score":        movie.get("score"),
#     }


# # ─────────────────────────────────────────────
# # COMPONENT: Hero banner
# # Built entirely with st.image + st.markdown (no nested HTML blocks).
# # The backdrop is rendered by Streamlit; the overlay text sits below
# # using absolute-position CSS on a wrapper div that contains ONLY
# # self-contained, non-nested markdown snippets.
# # ─────────────────────────────────────────────
# def render_hero(backdrop_url: str, title: str, overview: str,
#                 genres: list, year: str, rating: float = None, height: int = 400):
#     """
#     Renders a full-bleed hero. Uses st.image inside a CSS-positioned
#     wrapper so Streamlit controls the <img> element.
#     """
#     # pill HTML — all inline, no nested divs
#     pills = "".join(
#         f'<span class="cm-pill">{g["name"]}</span>'
#         for g in (genres or [])[:4]
#     )
#     overview_safe = (overview or "")[:380].replace("<", "&lt;").replace(">", "&gt;")

#     rating_block = ""
#     if rating:
#         rating_block = (
#             f'<div style="display:inline-block;margin-left:20px;">'
#             f'<div class="cm-stat-label">Rating</div>'
#             f'<div class="cm-stat-val">★ {rating:.1f}</div>'
#             f'</div>'
#         )

#     # Outer wrapper: relative position container
#     st.markdown(
#         f'<div class="cm-hero" style="height:{height}px;">',
#         unsafe_allow_html=True,
#     )

#     # Backdrop via st.image — Streamlit owns the img tag
#     st.image(backdrop_url, width=None)           # width=None → CSS controls sizing

#     # Overlay text — absolutely positioned over the image
#     # All content is in ONE self-contained markdown call (no open/unclosed tags)
#     st.markdown(f"""
# <div class="cm-hero-overlay">
#   <div class="cm-hero-inner">
#     <div class="cm-genre-row">{pills}</div>
#     <div class="cm-hero-title">{title}</div>
#     <div class="cm-hero-overview">{overview_safe}</div>
#     <div class="cm-hero-stats">
#       <div style="display:inline-block;">
#         <div class="cm-stat-label">Year</div>
#         <div class="cm-stat-val">{year or "—"}</div>
#       </div>
#       {rating_block}
#     </div>
#   </div>
# </div>
# """, unsafe_allow_html=True)

#     st.markdown('</div>', unsafe_allow_html=True)   # close .cm-hero


# # ─────────────────────────────────────────────
# # COMPONENT: Section header
# # ─────────────────────────────────────────────
# def section_header(title: str, label: str = ""):
#     lbl = f'<span class="cm-section-lbl">{label}</span>' if label else ""
#     st.markdown(f"""
# <div class="cm-section">
#   <h2>{title}</h2>
#   <div class="cm-section-div"></div>
#   {lbl}
# </div>""", unsafe_allow_html=True)


# # ─────────────────────────────────────────────
# # COMPONENT: Movie grid
# # Each card: st.image (native) + st.markdown for text body (self-contained)
# # ─────────────────────────────────────────────
# PLACEHOLDER = "https://placehold.co/300x450/141420/6B6B8A?text=No+Poster"

# def render_movie_grid(movies: List[Dict], cols: int = 6, show_score: bool = False):
#     if not movies:
#         st.markdown("""
# <div class="cm-empty">
#   <div class="ei">🎬</div>
#   <h3>No movies found</h3>
#   <p>Try a different search or category.</p>
# </div>""", unsafe_allow_html=True)
#         return

#     flat = [normalise(m) for m in movies]

#     for row_start in range(0, len(flat), cols):
#         row     = flat[row_start: row_start + cols]
#         columns = st.columns(cols, gap="small")

#         for ci, movie in enumerate(row):
#             with columns[ci]:
#                 title     = movie["title"]
#                 poster    = movie["poster_url"] or PLACEHOLDER
#                 year      = (movie["release_date"] or "")[:4] or "—"
#                 rating    = movie["vote_average"]
#                 score     = movie["score"]
#                 tmdb_id   = movie["tmdb_id"]

#                 # Card wrapper — opened here, closed at the bottom of this block
#                 st.markdown('<div class="cm-card">', unsafe_allow_html=True)

#                 # Poster: native Streamlit image, no use_container_width
#                 st.image(poster, width=None)

#                 # Card body — completely self-contained HTML, no open tags
#                 rating_str = f"★ {rating:.1f}" if rating else "—"
#                 score_span = (
#                     f'<span class="cm-score">{score:.2f}</span>'
#                     if show_score and score is not None else ""
#                 )
#                 st.markdown(f"""
# <div class="cm-card-body">
#   <div class="cm-card-title">{title}</div>
#   <div class="cm-card-meta">
#     <span class="cm-card-year">{year}</span>
#     <span class="cm-card-rating">{rating_str}</span>
#     {score_span}
#   </div>
# </div>""", unsafe_allow_html=True)

#                 # Details button
#                 if tmdb_id:
#                     if st.button("Details", key=f"btn_{tmdb_id}_{row_start}_{ci}"):
#                         st.session_state["selected_tmdb_id"] = int(tmdb_id)
#                         st.session_state["selected_title"]   = title
#                         st.session_state["goto_page"]        = "Details"
#                         st.rerun()

#                 st.markdown('</div>', unsafe_allow_html=True)   # close .cm-card


# # ─────────────────────────────────────────────
# # PAGES
# # ─────────────────────────────────────────────
# def page_home():
#     cat_map = {
#         "🔥 Trending":    "trending",
#         "⭐ Top Rated":   "top_rated",
#         "🎬 Now Playing": "now_playing",
#         "📅 Upcoming":    "upcoming",
#         "🍿 Popular":     "popular",
#     }
#     c1, c2 = st.columns([3, 1])
#     with c1:
#         st.markdown('<h1 class="cm-page-title">Discover Films</h1>', unsafe_allow_html=True)
#         st.markdown('<p class="cm-page-sub">Find your next watch from the world\'s best movies</p>',
#                     unsafe_allow_html=True)
#     with c2:
#         cat_label = st.selectbox("", list(cat_map.keys()), label_visibility="hidden")

#     category = cat_map[cat_label]
#     with st.spinner("Loading movies…"):
#         movies = get_home_feed(category, limit=24)
#     if not movies:
#         return

#     hero = movies[0]
#     if hero.get("poster_url"):
#         render_hero(
#             backdrop_url=hero["poster_url"].replace("/w500/", "/w1280/"),
#             title=hero.get("title", ""),
#             overview="",
#             genres=[],
#             year=(hero.get("release_date") or "")[:4],
#             rating=hero.get("vote_average"),
#             height=380,
#         )

#     section_header(f"{cat_label.split(' ', 1)[1]} Movies", f"{len(movies)} films")
#     render_movie_grid(movies[1:], cols=6)


# def page_search():
#     st.markdown('<h1 class="cm-page-title">Search & Discover</h1>', unsafe_allow_html=True)
#     st.markdown('<p class="cm-page-sub">Search for any film to get TF-IDF and genre-based recommendations</p>',
#                 unsafe_allow_html=True)

#     c1, c2 = st.columns([5, 1])
#     with c1:
#         query = st.text_input("", placeholder="e.g. The Dark Knight, Inception…",
#                               label_visibility="hidden", key="search_input")
#     with c2:
#         st.markdown("<br>", unsafe_allow_html=True)
#         do_search = st.button("Search", use_container_width=True)

#     if query and (do_search or st.session_state.get("last_search") == query):
#         st.session_state["last_search"] = query

#         section_header("Search Results", "TMDB")
#         with st.spinner("Searching TMDB…"):
#             raw = search_movies(query)
#         if raw and raw.get("results"):
#             cards = [
#                 {
#                     "title":        m.get("title", ""),
#                     "poster_url":   f"https://image.tmdb.org/t/p/w500{m['poster_path']}"
#                                     if m.get("poster_path") else None,
#                     "release_date": m.get("release_date"),
#                     "vote_average": m.get("vote_average"),
#                     "tmdb_id":      m.get("id"),
#                 }
#                 for m in raw["results"][:12]
#             ]
#             render_movie_grid(cards, cols=6)

#         st.markdown("<br>", unsafe_allow_html=True)
#         section_header("AI Recommendations", "TF-IDF + Genre")
#         with st.spinner("Fetching recommendations…"):
#             bundle = get_search_bundle(query)

#         if bundle:
#             details    = bundle.get("movie_details", {})
#             tfidf_recs = bundle.get("tfidf_recommendations", [])
#             genre_recs = bundle.get("genre_recommendations", [])

#             if details.get("backdrop_url"):
#                 render_hero(
#                     backdrop_url=details["backdrop_url"],
#                     title=details.get("title", ""),
#                     overview=details.get("overview", ""),
#                     genres=details.get("genres", []),
#                     year=(details.get("release_date") or "")[:4],
#                     height=280,
#                 )

#             tab1, tab2 = st.tabs(["🧠  Content-Based (TF-IDF)", "🎭  Same Genre"])
#             with tab1:
#                 if tfidf_recs:
#                     render_movie_grid(tfidf_recs, cols=6, show_score=True)
#                 else:
#                     st.markdown("""<div class="cm-empty"><div class="ei">🤔</div>
# <h3>No TF-IDF matches</h3><p>This title may not be in the local dataset.</p></div>""",
#                                 unsafe_allow_html=True)
#             with tab2:
#                 if genre_recs:
#                     render_movie_grid(genre_recs, cols=6)
#                 else:
#                     st.markdown("""<div class="cm-empty"><div class="ei">🎭</div>
# <h3>No genre recommendations</h3><p>Could not find genre data for this film.</p></div>""",
#                                 unsafe_allow_html=True)
#         else:
#             st.markdown("""<div class="cm-empty"><div class="ei">⚠️</div>
# <h3>Recommendations unavailable</h3><p>The backend may be busy — try again.</p></div>""",
#                         unsafe_allow_html=True)
#     else:
#         st.markdown("""
# <div class="cm-empty" style="margin-top:60px;">
#   <div class="ei">🔍</div>
#   <h3>Search for a film to get started</h3>
#   <p>Type a movie title above and press Search.</p>
# </div>""", unsafe_allow_html=True)


# def page_details():
#     tmdb_id        = st.session_state.get("selected_tmdb_id")
#     selected_title = st.session_state.get("selected_title", "")

#     if not tmdb_id:
#         st.markdown("""<div class="cm-empty" style="margin-top:80px;">
# <div class="ei">🎬</div><h3>No film selected</h3>
# <p>Click "Details" on any movie card to open this page.</p></div>""", unsafe_allow_html=True)
#         return

#     with st.spinner("Loading film…"):
#         details = get_movie_details(tmdb_id)
#         bundle  = get_search_bundle(selected_title) if selected_title else None

#     if not details:
#         st.error("Could not load movie details.")
#         return

#     if details.get("backdrop_url"):
#         render_hero(
#             backdrop_url=details["backdrop_url"],
#             title=details.get("title", ""),
#             overview=details.get("overview", ""),
#             genres=details.get("genres", []),
#             year=(details.get("release_date") or "")[:4],
#             height=460,
#         )

#     col_poster, col_info = st.columns([1, 3], gap="large")
#     with col_poster:
#         if details.get("poster_url"):
#             st.image(details["poster_url"], width=None)

#     with col_info:
#         year       = (details.get("release_date") or "")[:4]
#         genres_str = " · ".join(g["name"] for g in details.get("genres", []))
#         overview   = (details.get("overview") or "No overview available.").replace("<", "&lt;").replace(">", "&gt;")

#         st.markdown(f'<div class="cm-detail-title">{details.get("title","")}</div>',
#                     unsafe_allow_html=True)
#         st.markdown(f'<p style="color:#9090B0;font-size:13px;margin-bottom:14px;">{genres_str}</p>',
#                     unsafe_allow_html=True)
#         st.markdown(f'<p class="cm-detail-overview">{overview}</p>',
#                     unsafe_allow_html=True)

#         sc1, sc2 = st.columns(2)
#         with sc1:
#             st.markdown(f"""
# <div class="cm-stat-card">
#   <div class="cm-stat-card-val">{year}</div>
#   <div class="cm-stat-card-label">Release Year</div>
# </div>""", unsafe_allow_html=True)
#         with sc2:
#             rd = details.get("release_date", "Unknown")
#             st.markdown(f"""
# <div class="cm-stat-card">
#   <div class="cm-stat-card-val" style="font-size:17px;">{rd}</div>
#   <div class="cm-stat-card-label">Release Date</div>
# </div>""", unsafe_allow_html=True)

#     if bundle:
#         tfidf_recs = bundle.get("tfidf_recommendations", [])
#         genre_recs = bundle.get("genre_recommendations", [])
#         if tfidf_recs:
#             section_header("Because You Liked This", "TF-IDF Content Matching")
#             render_movie_grid(tfidf_recs, cols=6, show_score=True)
#         if genre_recs:
#             section_header("More in This Genre", "TMDB Discovery")
#             render_movie_grid(genre_recs, cols=6)


# def page_trending():
#     st.markdown('<h1 class="cm-page-title">Trending Today</h1>', unsafe_allow_html=True)
#     st.markdown('<p class="cm-page-sub">What the world is watching right now</p>', unsafe_allow_html=True)
#     with st.spinner("Loading…"):
#         movies = get_home_feed("trending", limit=24)
#     if movies:
#         render_movie_grid(movies, cols=6)


# def page_top_rated():
#     st.markdown('<h1 class="cm-page-title">Top Rated</h1>', unsafe_allow_html=True)
#     st.markdown('<p class="cm-page-sub">The all-time greats, as rated by audiences worldwide</p>', unsafe_allow_html=True)
#     with st.spinner("Loading…"):
#         movies = get_home_feed("top_rated", limit=24)
#     if movies:
#         render_movie_grid(movies, cols=6)


# # ─────────────────────────────────────────────
# # SIDEBAR
# # ─────────────────────────────────────────────
# page_map = {
#     "🏠  Home":      "Home",
#     "🔍  Search":    "Search",
#     "🔥  Trending":  "Trending",
#     "⭐  Top Rated": "Top Rated",
#     "🎬  Details":   "Details",
# }

# with st.sidebar:
#     st.markdown("""
# <div class="nav-brand">
#   <h1>CineMatch</h1>
#   <p>Film Discovery Engine</p>
# </div>""", unsafe_allow_html=True)

#     api_ok = health_check()
#     sc, st_txt = ("#4CAF50", "API Connected") if api_ok else ("#E53935", "API Offline")
#     st.markdown(
#         f'<p style="padding:6px 20px 12px;font-size:11px;color:{sc};">● {st_txt}</p>',
#         unsafe_allow_html=True,
#     )

#     nav = st.radio("Navigation", list(page_map.keys()), key="nav", label_visibility="hidden")

#     st.markdown("<br>" * 3, unsafe_allow_html=True)
#     st.markdown(
#         '<p style="padding:8px 20px;font-size:10px;color:#3A3A5A;letter-spacing:0.5px;">POWERED BY TMDB & TF-IDF</p>',
#         unsafe_allow_html=True,
#     )


# # ─────────────────────────────────────────────
# # ROUTER
# # ─────────────────────────────────────────────
# goto         = st.session_state.pop("goto_page", None)
# current_page = goto if goto else page_map[nav]

# if current_page == "Home":        page_home()
# elif current_page == "Search":    page_search()
# elif current_page == "Trending":  page_trending()
# elif current_page == "Top Rated": page_top_rated()
# elif current_page == "Details":   page_details()
import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_BASE = "http://localhost:8000"
# Generous timeout — bundle endpoint makes ~12 sequential TMDB calls
TIMEOUT  = 60

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
        return f"https://image.tmdb.org/t/p/w300{m['poster_path']}"
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
                "poster_url":   f"https://image.tmdb.org/t/p/w300{m['poster_path']}"
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
                "poster_url":   f"https://image.tmdb.org/t/p/w300{m['poster_path']}"
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