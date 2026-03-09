import random
import time
import urllib.parse

import gspread
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# =========================================================
# SNIFFLAB
# Mobile-first fragrance layering app
# =========================================================

CSV_PATH = "data/fragrances_master.csv"
AFFILIATE_TAG = "christacket04-20"

st.set_page_config(
    page_title="SniffLab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# THEME PRESETS
# =========================================================
THEMES = {
    "System Default": None,
    "Midnight": {
        "bg": "#050816",
        "card": "#111827",
        "text": "#F9FAFB",
        "muted": "#9CA3AF",
        "accent": "#8B5CF6",
        "border": "#374151",
        "button_bg": "#111827",
        "button_text": "#F9FAFB",
        "button_hover_bg": "#8B5CF6",
        "button_hover_text": "#050816",
    },
    "Pink Pretty": {
        "bg": "#FFF7FB",
        "card": "#FFE4F1",
        "text": "#5B2145",
        "muted": "#9D4D7B",
        "accent": "#EC4899",
        "border": "#F9A8D4",
        "button_bg": "#C0266D",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#EC4899",
        "button_hover_text": "#FFFFFF",
    },
    "Monochrome": {
        "bg": "#111111",
        "card": "#1F1F1F",
        "text": "#F5F5F5",
        "muted": "#BDBDBD",
        "accent": "#E5E7EB",
        "border": "#444444",
        "button_bg": "#1F1F1F",
        "button_text": "#F5F5F5",
        "button_hover_bg": "#E5E7EB",
        "button_hover_text": "#111111",
    },
    "Rainbow Pop": {
        "bg": "#0F172A",
        "card": "#111827",
        "text": "#F8FAFC",
        "muted": "#CBD5E1",
        "accent": "#22D3EE",
        "border": "#A78BFA",
        "button_bg": "#6D28D9",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#22D3EE",
        "button_hover_text": "#0F172A",
    },
}

# =========================================================
# SESSION STATE DEFAULTS
# =========================================================
DEFAULTS = {
    "theme_name": "System Default",
    "page": "Home",
    "my_collection": [],
    "sniff_list": [],
    "saved_combos": [],
    "combo_ratings": {},
    "latest_combos": [],
    "last_added": "",
    "search_query": "",
    "brand_filter": "All Brands",
    "source_mode": "My Collection",
    "vibe": "Any",
    "profile": "Any",
    "intensity": "Signature",
    "mixing_style": "Balanced",
    "browse_selected": [],
    "collection_selected": [],
    "collection_loaded_for_user": "",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

theme = THEMES[st.session_state.theme_name]

# =========================================================
# GOOGLE SHEETS CONNECTION
# =========================================================
@st.cache_resource
def get_gsheets_conn():
    return st.connection("gsheets", type=GSheetsConnection)


def run_with_backoff(func, max_retries: int = 5):
    """Retry Google Sheets operations when rate limits are hit."""
    for attempt in range(max_retries):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            msg = str(e).lower()
            if "429" in msg or "quota" in msg or "resource_exhausted" in msg:
                sleep_for = min((2 ** attempt) + random.random(), 10)
                time.sleep(sleep_for)
                continue
            raise
    raise RuntimeError("Google Sheets is temporarily busy. Please wait a moment and try again.")


# =========================================================
# AUTH + USER HELPERS
# =========================================================
@st.cache_data(ttl=30, show_spinner=False)
def load_users_sheet() -> pd.DataFrame:
    """Read the users worksheet and normalize its columns."""
    try:
        conn = get_gsheets_conn()
        df = run_with_backoff(lambda: conn.read(worksheet="users", ttl=30))
    except Exception:
        df = pd.DataFrame(columns=["user_id", "email", "display_name", "created_at"])

    if df is None or len(df) == 0:
        df = pd.DataFrame(columns=["user_id", "email", "display_name", "created_at"])
    else:
        df = pd.DataFrame(df).fillna("")

    for col in ["user_id", "email", "display_name", "created_at"]:
        if col not in df.columns:
            df[col] = ""

    return df[["user_id", "email", "display_name", "created_at"]].copy()


def save_users_sheet(users_df: pd.DataFrame) -> None:
    """Write the users worksheet back to Google Sheets."""
    conn = get_gsheets_conn()
    run_with_backoff(lambda: conn.update(worksheet="users", data=users_df))
    st.cache_data.clear()


def get_logged_in_identity():
    """Return the currently signed-in user's identity info."""
    if not st.user.is_logged_in:
        return None

    email = str(getattr(st.user, "email", "") or "").strip().lower()
    name = str(getattr(st.user, "name", "") or "").strip()

    if not email:
        return None

    if not name:
        name = email.split("@")[0]

    return {
        "user_id": email,
        "email": email,
        "display_name": name,
    }


def get_or_create_current_user():
    """Ensure the logged-in user exists in the users worksheet."""
    identity = get_logged_in_identity()
    if identity is None:
        return None

    users_df = load_users_sheet()

    existing = users_df[
        users_df["user_id"].astype(str).str.lower() == identity["user_id"]
    ]
    if not existing.empty:
        row = existing.iloc[0]
        return {
            "user_id": str(row["user_id"]),
            "email": str(row["email"]),
            "display_name": str(row["display_name"]),
        }

    new_row = pd.DataFrame([{
        "user_id": identity["user_id"],
        "email": identity["email"],
        "display_name": identity["display_name"],
        "created_at": pd.Timestamp.utcnow().isoformat(),
    }])

    users_df = pd.concat([users_df, new_row], ignore_index=True)
    save_users_sheet(users_df)
    return identity


# =========================================================
# COLLECTION STORAGE HELPERS
# =========================================================
@st.cache_data(ttl=30, show_spinner=False)
def load_collections_sheet() -> pd.DataFrame:
    """Read the collections worksheet and normalize its columns."""
    try:
        conn = get_gsheets_conn()
        df = run_with_backoff(lambda: conn.read(worksheet="collections", ttl=30))
    except Exception:
        df = pd.DataFrame(columns=["user_id", "fragrance_id", "fragrance_name", "brand", "added_at"])

    if df is None or len(df) == 0:
        df = pd.DataFrame(columns=["user_id", "fragrance_id", "fragrance_name", "brand", "added_at"])
    else:
        df = pd.DataFrame(df).fillna("")

    for col in ["user_id", "fragrance_id", "fragrance_name", "brand", "added_at"]:
        if col not in df.columns:
            df[col] = ""

    return df[["user_id", "fragrance_id", "fragrance_name", "brand", "added_at"]].copy()


def save_collections_sheet(collections_df: pd.DataFrame) -> None:
    """Write the collections worksheet back to Google Sheets."""
    conn = get_gsheets_conn()
    run_with_backoff(lambda: conn.update(worksheet="collections", data=collections_df))
    st.cache_data.clear()


def load_user_collection(user_id: str) -> list[str]:
    """Return this user's saved collection as a list of display names."""
    collections_df = load_collections_sheet()
    if collections_df.empty:
        return []

    user_rows = collections_df[
        collections_df["user_id"].astype(str).str.lower() == str(user_id).strip().lower()
    ].copy()

    if user_rows.empty:
        return []

    items = user_rows["fragrance_name"].astype(str).tolist()
    return [x for x in items if x.strip()]


def add_collection_item(user_id: str, row) -> None:
    """Add one fragrance to the user's collection in Google Sheets."""
    collections_df = load_collections_sheet()

    fragrance_id = str(row["id"])
    fragrance_name = str(row["display_name"])
    brand = str(row["brand_pretty"])

    already_exists = collections_df[
        (collections_df["user_id"].astype(str).str.lower() == str(user_id).strip().lower()) &
        (collections_df["fragrance_id"].astype(str) == fragrance_id)
    ]

    if not already_exists.empty:
        return

    new_row = pd.DataFrame([{
        "user_id": user_id,
        "fragrance_id": fragrance_id,
        "fragrance_name": fragrance_name,
        "brand": brand,
        "added_at": pd.Timestamp.utcnow().isoformat(),
    }])

    collections_df = pd.concat([collections_df, new_row], ignore_index=True)
    save_collections_sheet(collections_df)


def remove_collection_item(user_id: str, fragrance_name: str) -> None:
    """Remove one fragrance from the user's collection in Google Sheets."""
    collections_df = load_collections_sheet()

    collections_df = collections_df[
        ~(
            (collections_df["user_id"].astype(str).str.lower() == str(user_id).strip().lower()) &
            (collections_df["fragrance_name"].astype(str) == str(fragrance_name))
        )
    ].copy()

    save_collections_sheet(collections_df)


def sync_session_collection_from_cloud(user_id: str) -> None:
    """Load the user's saved collection into session state."""
    st.session_state.my_collection = load_user_collection(user_id)


# =========================================================
# STYLING
# =========================================================
if theme is not None:
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-color: {theme['bg']};
                color: {theme['text']};
            }}

            .main-title {{
                font-size: 2rem;
                font-weight: 800;
                margin-bottom: 0.10rem;
                color: {theme['text']};
            }}

            .sub-title {{
                font-size: 1rem;
                color: {theme['muted']};
                margin-bottom: 0.75rem;
            }}

            .hint-box {{
                background: {theme['card']};
                border: 1px solid {theme['border']};
                border-radius: 16px;
                padding: 12px 14px;
                margin-bottom: 12px;
                color: {theme['muted']};
                font-size: 0.95rem;
            }}

            .hero-box {{
                background: {theme['card']};
                border: 1px solid {theme['border']};
                border-radius: 20px;
                padding: 16px;
                margin-bottom: 14px;
            }}

            .sniff-card {{
                background: {theme['card']};
                border: 1px solid {theme['border']};
                border-radius: 18px;
                padding: 14px;
                margin-bottom: 10px;
            }}

            .sniff-name {{
                font-size: 1.05rem;
                font-weight: 700;
                color: {theme['text']};
                margin-bottom: 0.2rem;
            }}

            .sniff-name .sniff-meta {{
                font-size: 0.95rem;
                font-weight: 500;
                opacity: 0.85;
            }}

            .mini-label {{
                color: {theme['muted']};
                font-size: 0.82rem;
                margin-bottom: 0.1rem;
            }}

            .collection-chip {{
                background: {theme['card']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
                padding: 10px 12px;
                margin-bottom: 8px;
            }}

            .tier-chip {{
                display: inline-block;
                padding: 4px 10px;
                border-radius: 999px;
                background: {theme['accent']};
                color: {theme['button_hover_text']};
                font-size: 0.8rem;
                font-weight: 700;
                margin-bottom: 8px;
            }}

            div.stButton > button {{
                background-color: {theme['button_bg']} !important;
                color: {theme['button_text']} !important;
                border: 1px solid {theme['border']} !important;
                border-radius: 12px !important;
                min-height: 44px !important;
                font-size: 18px !important;
                box-shadow: none !important;
                -webkit-text-fill-color: {theme['button_text']} !important;
            }}

            div.stButton > button p,
            div.stButton > button span,
            div.stButton > button div {{
                color: {theme['button_text']} !important;
                -webkit-text-fill-color: {theme['button_text']} !important;
            }}

            div.stButton > button:hover {{
                background-color: {theme['button_hover_bg']} !important;
                color: {theme['button_hover_text']} !important;
                border-color: {theme['button_hover_bg']} !important;
                -webkit-text-fill-color: {theme['button_hover_text']} !important;
            }}

            div.stButton > button:hover p,
            div.stButton > button:hover span,
            div.stButton > button:hover div {{
                color: {theme['button_hover_text']} !important;
                -webkit-text-fill-color: {theme['button_hover_text']} !important;
            }}

            div.stButton > button[kind="primary"] {{
                background-color: {theme['accent']} !important;
                color: {theme['button_hover_text']} !important;
                border-color: {theme['accent']} !important;
                font-weight: 700 !important;
                -webkit-text-fill-color: {theme['button_hover_text']} !important;
            }}

            div.stButton > button[kind="primary"] p,
            div.stButton > button[kind="primary"] span,
            div.stButton > button[kind="primary"] div {{
                color: {theme['button_hover_text']} !important;
                -webkit-text-fill-color: {theme['button_hover_text']} !important;
            }}

            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div {{
                background-color: {theme['card']} !important;
                border-color: {theme['border']} !important;
                color: {theme['text']} !important;
                border-radius: 12px !important;
            }}

            input {{
                color: {theme['text']} !important;
                -webkit-text-fill-color: {theme['text']} !important;
            }}

            .stLinkButton a {{
                background-color: {theme['button_bg']} !important;
                color: {theme['button_text']} !important;
                border: 1px solid {theme['border']} !important;
                border-radius: 12px !important;
                min-height: 44px !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-decoration: none !important;
                -webkit-text-fill-color: {theme['button_text']} !important;
            }}

            .stLinkButton a:hover {{
                background-color: {theme['button_hover_bg']} !important;
                color: {theme['button_hover_text']} !important;
                border-color: {theme['button_hover_bg']} !important;
                -webkit-text-fill-color: {theme['button_hover_text']} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# DATA HELPERS
# =========================================================
@st.cache_data
def load_fragrances() -> pd.DataFrame:
    """Load and enrich the fragrance catalog for display and scoring."""
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

    def pretty_text(value: str) -> str:
        value = str(value).replace("-", " ").replace("_", " ").strip()
        return " ".join(word.capitalize() for word in value.split())

    def split_notes(value: str) -> list[str]:
        if not value:
            return []
        return [x.strip() for x in str(value).split(";") if x.strip()]

    def infer_family(row) -> str:
        text = " ".join([
            row.get("mainaccord1", ""),
            row.get("mainaccord2", ""),
            row.get("mainaccord3", ""),
            row.get("mainaccord4", ""),
            row.get("mainaccord5", ""),
            row.get("top_notes", ""),
            row.get("middle_notes", ""),
            row.get("base_notes", ""),
        ]).lower()

        if any(x in text for x in ["gourmand", "sweet", "vanilla", "dessert", "marzipan", "milky", "caramel", "chocolate"]):
            return "Gourmand"
        if any(x in text for x in ["floral", "rose", "jasmine", "orange blossom", "neroli", "iris", "peony", "tuberose"]):
            return "Floral"
        if any(x in text for x in ["citrus", "fresh", "marine", "mint", "bergamot", "lemon", "grapefruit", "aquatic"]):
            return "Fresh"
        if any(x in text for x in ["woody", "amber", "tobacco", "cedar", "sandalwood", "oud", "incense", "patchouli", "warm spicy"]):
            return "Woody / Warm"
        if any(x in text for x in ["fruity", "pear", "mango", "cherry", "lychee", "peach", "plum", "strawberry"]):
            return "Fruity"
        return "Other"

    df["name_pretty"] = df["name"].apply(pretty_text)
    df["brand_pretty"] = df["brand"].apply(pretty_text)
    df["display_name"] = df["name_pretty"] + " — " + df["brand_pretty"]

    df["top_list"] = df["top_notes"].apply(split_notes)
    df["middle_list"] = df["middle_notes"].apply(split_notes)
    df["base_list"] = df["base_notes"].apply(split_notes)

    df["accords"] = df[["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]].apply(
        lambda row: [x.strip().lower() for x in row.tolist() if str(x).strip()],
        axis=1,
    )

    df["all_notes"] = df.apply(
        lambda row: list(dict.fromkeys(row["top_list"] + row["middle_list"] + row["base_list"])),
        axis=1,
    )

    df["family"] = df.apply(infer_family, axis=1)

    df["search_text"] = (
        df["name"].str.lower() + " " +
        df["brand"].str.lower() + " " +
        df["inspired_by"].str.lower() + " " +
        df["top_notes"].str.lower() + " " +
        df["middle_notes"].str.lower() + " " +
        df["base_notes"].str.lower() + " " +
        df["mainaccord1"].str.lower() + " " +
        df["mainaccord2"].str.lower() + " " +
        df["mainaccord3"].str.lower() + " " +
        df["mainaccord4"].str.lower() + " " +
        df["mainaccord5"].str.lower()
    )

    return df


def family_icon(family: str) -> str:
    return {
        "Gourmand": "🧁",
        "Floral": "🌸",
        "Fresh": "🍋",
        "Woody / Warm": "🪵",
        "Fruity": "🍒",
        "Other": "🧪",
    }.get(family, "🧪")


def amazon_search_link(query: str) -> str:
    return f"https://www.amazon.com/s?k={urllib.parse.quote_plus(query)}&tag={AFFILIATE_TAG}"


# =========================================================
# COMBO ENGINE
# =========================================================
def combo_score(a, b, vibe, profile, intensity, mixing_style) -> float:
    accords_a = set(a["accords"])
    accords_b = set(b["accords"])
    notes_a = set([x.lower() for x in a["all_notes"]])
    notes_b = set([x.lower() for x in b["all_notes"]])

    shared_accords = accords_a & accords_b
    shared_notes = notes_a & notes_b

    score = 0.0
    score += len(shared_accords) * 2.8
    score += len(shared_notes) * 1.2

    combined = " ".join(list(accords_a | accords_b) + list(notes_a | notes_b))

    bridge_pairs = [
        (["vanilla", "amber"], 2.5),
        (["coffee", "vanilla"], 2.2),
        (["cherry", "almond"], 2.3),
        (["tobacco", "vanilla"], 2.5),
        (["floral", "musk"], 1.8),
        (["citrus", "fresh"], 1.6),
        (["woody", "amber"], 2.0),
        (["gourmand", "sweet"], 2.0),
        (["rose", "lychee"], 2.0),
        (["marshmallow", "orange blossom"], 2.0),
        (["bergamot", "woods"], 1.5),
        (["marine", "citrus"], 1.4),
    ]
    for needed, pts in bridge_pairs:
        if all(term in combined for term in needed):
            score += pts

    bridge_count = len(shared_accords) + len(shared_notes)
    if bridge_count == 0:
        score -= 3.0
    elif bridge_count == 1:
        score -= 0.8
    else:
        score += 1.0

    risky_pairs = [
        (["marine", "chocolate"], 1.8),
        (["marine", "caramel"], 1.5),
        (["oud", "aquatic"], 1.4),
        (["citrus", "smoke"], 1.0),
    ]
    for needed, penalty in risky_pairs:
        if all(term in combined for term in needed) and bridge_count < 2:
            score -= penalty

    base_a = set([x.lower() for x in a["base_list"]])
    base_b = set([x.lower() for x in b["base_list"]])
    middle_a = set([x.lower() for x in a["middle_list"]])
    middle_b = set([x.lower() for x in b["middle_list"]])

    score += len(base_a & base_b) * 1.8
    score += len(middle_a & middle_b) * 1.0

    vibe_terms = {
        "Any": [],
        "Sexy": ["amber", "vanilla", "musk", "tobacco", "warm spicy"],
        "Clean": ["fresh", "citrus", "marine", "bergamot", "mint", "white musk"],
        "Cozy": ["gourmand", "vanilla", "sweet", "milky", "amber"],
        "Night Out": ["boozy", "amber", "woody", "musk", "vanilla"],
        "Soft": ["floral", "musk", "powdery", "rose", "jasmine"],
    }

    profile_terms = {
        "Any": [],
        "Gourmand": ["gourmand", "sweet", "dessert", "vanilla", "caramel", "chocolate"],
        "Floral": ["floral", "rose", "jasmine", "orange blossom", "neroli", "iris"],
        "Fresh": ["fresh", "citrus", "marine", "bergamot", "grapefruit", "mint"],
        "Woody": ["woody", "cedar", "sandalwood", "patchouli", "incense"],
        "Fruity": ["fruity", "pear", "mango", "cherry", "lychee", "plum"],
    }

    for term in vibe_terms.get(vibe, []):
        if term in combined:
            score += 0.8

    for term in profile_terms.get(profile, []):
        if term in combined:
            score += 0.9

    if intensity == "Easy":
        if len(shared_accords) >= 2:
            score += 1.2
        if bridge_count < 2:
            score -= 0.6
    elif intensity == "Signature":
        if len(shared_accords) >= 1 and bridge_count >= 2:
            score += 1.4
    elif intensity == "Beast Mode":
        if any(x in combined for x in ["amber", "vanilla", "tobacco", "oud", "coffee", "boozy"]):
            score += 2.0
        if len(base_a & base_b) >= 1:
            score += 1.0
    elif intensity == "Experimental":
        if bridge_count >= 1:
            score += 0.5

    same_brand = str(a["brand"]).strip().lower() == str(b["brand"]).strip().lower()
    if mixing_style == "Same House":
        score += 2.0 if same_brand else -1.5
    elif mixing_style == "Cross-House":
        score += 2.0 if not same_brand else -1.5
    elif mixing_style == "Balanced":
        score += 0.5 if same_brand else 0.8

    return round(score, 2)


def combo_tier(score: float, intensity: str) -> str:
    if intensity == "Beast Mode":
        return "Beast Mode" if score >= 10 else "Signature Blend"
    if intensity == "Experimental":
        return "Wild Card" if score >= 9 else "Experimental"
    if score >= 10:
        return "Signature Blend"
    if score >= 8:
        return "Easy Win"
    if score >= 6.5:
        return "Date Night"
    return "Clean Flex"


def combo_name(a, b, tier: str) -> str:
    first = a["name_pretty"].split()[0]
    second = b["name_pretty"].split()[0]

    naming_bank = {
        "Beast Mode": ["After Dark", "Maximum Heat", "Velvet Storm", "Power Blend"],
        "Signature Blend": ["Golden Rush", "Velvet Heat", "Clean Rich", "Midnight Silk"],
        "Easy Win": ["Soft Glow", "Fresh Ease", "Daily Luxe", "Easy Spark"],
        "Date Night": ["Pink After Dark", "Night Bloom", "Sugar Smoke", "Velvet Kiss"],
        "Clean Flex": ["Bright Drift", "Clean Current", "Cool Linen", "Fresh Signal"],
        "Wild Card": ["Chaos Bloom", "Electric Cream", "Fever Dream", "Dark Candy"],
        "Experimental": ["Odd Magic", "Twist Mode", "Curveball", "Neon Dust"],
    }

    suffix = random.choice(naming_bank.get(tier, ["Blend"]))
    if first.lower() != second.lower():
        return f"{first} x {second}: {suffix}"
    return f"{first}: {suffix}"


def combo_description(a, b, vibe, profile) -> str:
    combined = " ".join(a["accords"] + b["accords"] + [x.lower() for x in a["all_notes"] + b["all_notes"]])

    if "gourmand" in combined or "vanilla" in combined:
        return f"A creamy, sweeter layering idea with a {vibe.lower() if vibe != 'Any' else 'smooth'} feel."
    if "floral" in combined or "rose" in combined or "jasmine" in combined:
        return f"A lifted floral pairing with a {profile.lower() if profile != 'Any' else 'soft'} edge."
    if "fresh" in combined or "citrus" in combined or "marine" in combined:
        return "A brighter, cleaner combination that should feel airy and easy to wear."
    if "woody" in combined or "amber" in combined or "tobacco" in combined:
        return "A richer blend with more depth, warmth, and presence."
    if "fruity" in combined or "cherry" in combined or "pear" in combined:
        return "A juicy, more playful combo with extra brightness and personality."
    return "A balanced blend built from shared structure and complementary notes."


# =========================================================
# LOAD DATA
# =========================================================
df = load_fragrances()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("SniffLab")

    valid_pages = ["Home", "Browse", "Collection", "Saved", "Help", "Settings"]
    current_page = st.session_state.page if st.session_state.page in valid_pages else "Home"

    page = st.radio("Go to", valid_pages, index=valid_pages.index(current_page))
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()

    st.divider()
    st.caption("As an Amazon Associate I earn from qualifying purchases.")

# =========================================================
# APP HEADER
# =========================================================
st.markdown('<div class="main-title">🧪