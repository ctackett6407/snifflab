import streamlit as st
import pandas as pd
import random
from pathlib import Path

# ============================================================
# SNIFFLAB
# Mobile-first fragrance discovery and layering app
# Built for simple Streamlit Cloud deployment
# ============================================================

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="SniffLab",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------
CATALOG_PATH = "fragrances_master.csv"

NAV_ITEMS = ["Home", "Browse", "Collection", "Sniff", "Saved"]

THEMES = {
    "System Default": None,  # Special case: disables custom CSS
    "Midnight": {
        "background": "#0E1117",
        "card": "#161B22",
        "text": "#F5F7FA",
        "muted": "#AAB2BF",
        "accent": "#5DADE2",
        "border": "#2A2F3A",
        "button_bg": "#1F6FEB",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#3B82F6",
        "button_hover_text": "#FFFFFF",
    },
    "Pink Pretty": {
        "background": "#FFF6FB",
        "card": "#FFFFFF",
        "text": "#2C2030",
        "muted": "#7D6C7B",
        "accent": "#E754A6",
        "border": "#F3C7DD",
        "button_bg": "#E754A6",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#C63D8B",
        "button_hover_text": "#FFFFFF",
    },
    "Monochrome": {
        "background": "#F7F7F7",
        "card": "#FFFFFF",
        "text": "#111111",
        "muted": "#666666",
        "accent": "#333333",
        "border": "#DDDDDD",
        "button_bg": "#111111",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#333333",
        "button_hover_text": "#FFFFFF",
    },
    "Rainbow Pop": {
        "background": "#FFFDF8",
        "card": "#FFFFFF",
        "text": "#222222",
        "muted": "#666666",
        "accent": "#FF4D6D",
        "border": "#E9E3D5",
        "button_bg": "#7C3AED",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#5B21B6",
        "button_hover_text": "#FFFFFF",
    }
}

# ------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ------------------------------------------------------------
def init_session_state():
    """Initialize all session state keys used by the app."""
    defaults = {
        "theme_name": "System Default",
        "page": "Home",
        "collection_ids": [],
        "saved_layerings": [],
        "search_query": "",
        "selected_brand": "All",
        "selected_category": "All",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------
@st.cache_data
def load_catalog(path: str) -> pd.DataFrame:
    """
    Load fragrance catalog from CSV.
    Adds a stable internal id if one does not exist.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        return pd.DataFrame(columns=["id", "brand", "name", "accords", "notes", "category"])

    df = pd.read_csv(csv_path)

    # Normalize expected columns
    expected_columns = ["brand", "name", "accords", "notes", "category"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = ""

    # Create stable app id if missing
    if "id" not in df.columns:
        df["id"] = (
            df["brand"].fillna("").astype(str).str.strip().str.lower() + "||" +
            df["name"].fillna("").astype(str).str.strip().str.lower()
        )

    # Fill NaNs for safe display
    df = df.fillna("")

    return df


# ------------------------------------------------------------
# THEME / CSS
# ------------------------------------------------------------
def apply_theme(theme_name: str):
    """
    Applies custom CSS theme unless System Default is selected.
    System Default means: do not inject theme CSS at all.
    """
    theme = THEMES.get(theme_name)

    # Important behavior:
    # If System Default is selected, custom CSS is disabled.
    if theme is None:
        return

    st.markdown(
        f"""
        <style>
        /* ----------------------------------------------------
           ROOT APP STYLING
        ---------------------------------------------------- */
        .stApp {{
            background-color: {theme["background"]};
            color: {theme["text"]};
        }}

        html, body, [class*="css"] {{
            color: {theme["text"]};
        }}

        /* ----------------------------------------------------
           MOBILE SPACING / CONTENT WIDTH
        ---------------------------------------------------- */
        .block-container {{
            padding-top: 0.8rem;
            padding-bottom: 5rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            max-width: 760px;
        }}

        /* ----------------------------------------------------
           HEADINGS / TEXT
        ---------------------------------------------------- */
        h1, h2, h3, h4, h5, h6, p, label, span, div {{
            color: {theme["text"]};
        }}

        .snifflab-subtle {{
            color: {theme["muted"]};
            font-size: 0.95rem;
        }}

        /* ----------------------------------------------------
           CARD STYLING
        ---------------------------------------------------- */
        .sniff-card {{
            background: {theme["card"]};
            border: 1px solid {theme["border"]};
            border-radius: 16px;
            padding: 14px 14px 12px 14px;
            margin-bottom: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        }}

        .sniff-card-title {{
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 2px;
            color: {theme["text"]};
        }}

        .sniff-card-brand {{
            font-size: 0.9rem;
            color: {theme["muted"]};
            margin-bottom: 10px;
        }}

        .sniff-chip {{
            display: inline-block;
            background: {theme["background"]};
            border: 1px solid {theme["border"]};
            color: {theme["text"]};
            border-radius: 999px;
            padding: 4px 10px;
            margin: 2px 6px 2px 0;
            font-size: 0.78rem;
        }}

        /* ----------------------------------------------------
           BUTTONS
           This section is important because button text color
           must remain readable across all themes.
        ---------------------------------------------------- */
        .stButton > button {{
            width: 100%;
            border-radius: 12px;
            border: 1px solid {theme["border"]};
            background: {theme["button_bg"]};
            color: {theme["button_text"]} !important;
            font-weight: 600;
            min-height: 44px;
        }}

        .stButton > button * {{
            color: {theme["button_text"]} !important;
        }}

        .stButton > button:hover {{
            background: {theme["button_hover_bg"]};
            color: {theme["button_hover_text"]} !important;
            border: 1px solid {theme["border"]};
        }}

        .stButton > button:hover * {{
            color: {theme["button_hover_text"]} !important;
        }}

        /* ----------------------------------------------------
           INPUTS / SELECTS
        ---------------------------------------------------- */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{
            border-radius: 12px !important;
        }}

        /* ----------------------------------------------------
           SIDEBAR
        ---------------------------------------------------- */
        section[data-testid="stSidebar"] {{
            background: {theme["card"]};
            border-right: 1px solid {theme["border"]};
        }}

        /* ----------------------------------------------------
           HORIZONTAL RULE
        ---------------------------------------------------- */
        hr {{
            border-color: {theme["border"]};
        }}

        /* ----------------------------------------------------
           SMALL SCREEN TUNING
        ---------------------------------------------------- */
        @media (max-width: 640px) {{
            .block-container {{
                padding-top: 0.5rem;
                padding-left: 0.7rem;
                padding-right: 0.7rem;
            }}

            .sniff-card {{
                padding: 12px;
                border-radius: 14px;
            }}

            .sniff-card-title {{
                font-size: 1rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------
def get_collection_df(catalog_df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame of fragrances currently in the user's collection."""
    return catalog_df[catalog_df["id"].isin(st.session_state["collection_ids"])].copy()


def get_browse_df(catalog_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return DataFrame for Browse page.
    Important behavior:
    If fragrance is already in collection, hide it from Add/Browse list.
    """
    df = catalog_df[~catalog_df["id"].isin(st.session_state["collection_ids"])].copy()

    # Search
    query = st.session_state["search_query"].strip().lower()
    if query:
        search_blob = (
            df["brand"].astype(str).str.lower() + " " +
            df["name"].astype(str).str.lower() + " " +
            df["accords"].astype(str).str.lower() + " " +
            df["notes"].astype(str).str.lower() + " " +
            df["category"].astype(str).str.lower()
        )
        df = df[search_blob.str.contains(query, na=False)]

    # Brand filter
    if st.session_state["selected_brand"] != "All":
        df = df[df["brand"] == st.session_state["selected_brand"]]

    # Category filter
    if st.session_state["selected_category"] != "All":
        df = df[df["category"] == st.session_state["selected_category"]]

    return df


def add_to_collection(fragrance_id: str):
    """Add fragrance to collection if not already added."""
    if fragrance_id not in st.session_state["collection_ids"]:
        st.session_state["collection_ids"].append(fragrance_id)


def remove_from_collection(fragrance_id: str):
    """Remove fragrance from collection if present."""
    st.session_state["collection_ids"] = [
        fid for fid in st.session_state["collection_ids"] if fid != fragrance_id
    ]


def save_layering(layering: dict):
    """Save a layering suggestion to the Saved list."""
    existing = st.session_state["saved_layerings"]
    if layering not in existing:
        existing.append(layering)
        st.session_state["saved_layerings"] = existing


def render_chips(text_value: str):
    """Render comma-separated text as chips."""
    if not text_value:
        return

    parts = [p.strip() for p in str(text_value).split(",") if p.strip()]
    if not parts:
        return

    chips_html = "".join([f'<span class="sniff-chip">{p}</span>' for p in parts[:6]])
    st.markdown(chips_html, unsafe_allow_html=True)


def fragrance_card(row: pd.Series, mode: str = "browse"):
    """
    Reusable fragrance card.
    mode:
      - browse: show add button
      - collection: show remove button
    """
    st.markdown(
        f"""
        <div class="sniff-card">
            <div class="sniff-card-title">{row["name"]}</div>
            <div class="sniff-card-brand">{row["brand"]}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if str(row.get("category", "")).strip():
        st.caption(f"Category: {row['category']}")

    if str(row.get("accords", "")).strip():
        st.write("**Accords**")
        render_chips(row["accords"])

    if str(row.get("notes", "")).strip():
        st.write("**Notes**")
        render_chips(row["notes"])

    if mode == "browse":
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➕ Add", key=f"add_{row['id']}"):
                add_to_collection(row["id"])
                st.rerun()
        with col2:
            st.button("⭐ Save", key=f"save_catalog_{row['id']}", disabled=True)

    elif mode == "collection":
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✕ Remove", key=f"remove_{row['id']}"):
                remove_from_collection(row["id"])
                st.rerun()
        with col2:
            st.button("⭐ Save", key=f"save_collection_{row['id']}", disabled=True)


def generate_layering_suggestion(source_df: pd.DataFrame):
    """
    Very simple layering suggestion generator.
    This is intentionally lightweight and stable for now.
    Future versions can use accord matching, note compatibility,
    community voting, or weighted scoring.
    """
    if len(source_df) < 2:
        return None

    picks = source_df.sample(2, replace=False).to_dict("records")
    a, b = picks[0], picks[1]

    suggestion = {
        "name_1": a["name"],
        "brand_1": a["brand"],
        "name_2": b["name"],
        "brand_2": b["brand"],
        "summary": f"Try layering {a['name']} with {b['name']} for a fresh combo.",
        "id_pair": f"{a['id']}__{b['id']}"
    }
    return suggestion


# ------------------------------------------------------------
# SIDEBAR NAVIGATION
# ------------------------------------------------------------
def render_sidebar(catalog_df: pd.DataFrame):
    """Sidebar is the main navigation control for keeping the home screen clean."""
    with st.sidebar:
        st.title("🧪 SniffLab")

        st.write("Navigation")
        for item in NAV_ITEMS:
            if st.button(item, key=f"nav_{item}"):
                st.session_state["page"] = item
                st.rerun()

        st.markdown("---")

        st.write("Theme")
        selected_theme = st.selectbox(
            "Choose a theme",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state["theme_name"]),
            label_visibility="collapsed"
        )

        if selected_theme != st.session_state["theme_name"]:
            st.session_state["theme_name"] = selected_theme
            st.rerun()

        st.markdown("---")
        st.caption(f"Catalog size: {len(catalog_df)}")
        st.caption(f"My collection: {len(st.session_state['collection_ids'])}")


# ------------------------------------------------------------
# PAGE RENDERERS
# ------------------------------------------------------------
def render_home():
    """Minimal home page. No clutter."""
    st.title("SniffLab")
    st.write("Explore fragrances, build your collection, and generate layering ideas.")
    st.markdown('<p class="snifflab-subtle">Use the >> menu to browse, add, remove, and sniff combos.</p>', unsafe_allow_html=True)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Browse Fragrances"):
            st.session_state["page"] = "Browse"
            st.rerun()
    with c2:
        if st.button("Open Collection"):
            st.session_state["page"] = "Collection"
            st.rerun()


def render_browse(catalog_df: pd.DataFrame):
    """Browse page with minimal filters and hide-if-added behavior."""
    st.title("Browse")

    # Keep filtering simple for mobile
    st.session_state["search_query"] = st.text_input(
        "Search",
        value=st.session_state["search_query"],
        placeholder="Brand, fragrance, note..."
    )

    brands = ["All"] + sorted([b for b in catalog_df["brand"].dropna().unique() if str(b).strip()])
    categories = ["All"] + sorted([c for c in catalog_df["category"].dropna().unique() if str(c).strip()])

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["selected_brand"] = st.selectbox(
            "Brand",
            brands,
            index=brands.index(st.session_state["selected_brand"]) if st.session_state["selected_brand"] in brands else 0
        )
    with col2:
        st.session_state["selected_category"] = st.selectbox(
            "Category",
            categories,
            index=categories.index(st.session_state["selected_category"]) if st.session_state["selected_category"] in categories else 0
        )

    browse_df = get_browse_df(catalog_df)

    st.caption(f"{len(browse_df)} fragrances available to add")

    if browse_df.empty:
        st.info("Nothing to add right now. Your collection may already include the current matches.")
        return

    for _, row in browse_df.iterrows():
        fragrance_card(row, mode="browse")


def render_collection(catalog_df: pd.DataFrame):
    """User collection page with easy removal."""
    st.title("Collection")

    collection_df = get_collection_df(catalog_df)

    if collection_df.empty:
        st.info("Your collection is empty. Add fragrances from Browse.")
        return

    st.caption(f"{len(collection_df)} fragrances in your collection")

    for _, row in collection_df.iterrows():
        fragrance_card(row, mode="collection")


def render_sniff(catalog_df: pd.DataFrame):
    """Layering suggestion generator."""
    st.title("Sniff")

    collection_df = get_collection_df(catalog_df)

    source_mode = st.radio(
        "Choose source",
        ["My Collection", "Community Catalog"],
        horizontal=True
    )

    if source_mode == "My Collection":
        source_df = collection_df
        st.caption("Suggestions will use fragrances from your collection.")
    else:
        source_df = catalog_df
        st.caption("Suggestions will use the full community catalog.")

    if len(source_df) < 2:
        st.warning("You need at least 2 fragrances in the selected source to generate a layering suggestion.")
        return

    if st.button("🧪 Generate Layering"):
        suggestion = generate_layering_suggestion(source_df)

        if suggestion:
            st.markdown(
                f"""
                <div class="sniff-card">
                    <div class="sniff-card-title">{suggestion["name_1"]} + {suggestion["name_2"]}</div>
                    <div class="sniff-card-brand">{suggestion["brand_1"]} + {suggestion["brand_2"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write(suggestion["summary"])

            if st.button("⭐ Save This Combo"):
                save_layering(suggestion)
                st.success("Saved.")


def render_saved():
    """Saved layering suggestions."""
    st.title("Saved")

    saved = st.session_state["saved_layerings"]

    if not saved:
        st.info("No saved layerings yet.")
        return

    for i, item in enumerate(saved):
        st.markdown(
            f"""
            <div class="sniff-card">
                <div class="sniff-card-title">{item["name_1"]} + {item["name_2"]}</div>
                <div class="sniff-card-brand">{item["brand_1"]} + {item["brand_2"]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write(item["summary"])

        if st.button("✕ Remove Saved Combo", key=f"remove_saved_{i}"):
            st.session_state["saved_layerings"].pop(i)
            st.rerun()


# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
def main():
    init_session_state()

    catalog_df = load_catalog(CATALOG_PATH)

    # Apply theme after session state is initialized
    apply_theme(st.session_state["theme_name"])

    # Sidebar controls navigation, keeps main screen minimal
    render_sidebar(catalog_df)

    # Page router
    page = st.session_state["page"]

    if page == "Home":
        render_home()
    elif page == "Browse":
        render_browse(catalog_df)
    elif page == "Collection":
        render_collection(catalog_df)
    elif page == "Sniff":
        render_sniff(catalog_df)
    elif page == "Saved":
        render_saved()
    else:
        render_home()


if __name__ == "__main__":
    main()