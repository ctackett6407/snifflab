import random
import urllib.parse

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
# "System Default" means Streamlit's normal styling
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
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

theme = THEMES[st.session_state.theme_name]

# =========================================================
# GOOGLE SHEETS CONNECTION
# This connects to the private Google Sheet configured in
# Streamlit secrets under [connections.gsheets].
# =========================================================
@st.cache_resource
def get_gsheets_conn():
    return st.connection("gsheets", type=GSheetsConnection)

# =========================================================
# AUTH + USER HELPERS
# We use Google login through Streamlit auth.
# The signed-in user becomes the stable owner of
# collections, wishlist, combos, and ratings.
# =========================================================
@st.cache_data(ttl=0, show_spinner=False)
def load_users_sheet() -> pd.DataFrame:
    """Read the users worksheet and normalize its columns."""
    conn = get_gsheets_conn()
    df = conn.read(worksheet="users", ttl=0)

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
    conn.update(worksheet="users", data=users_df)
    st.cache_data.clear()


def get_logged_in_identity():
    """
    Return the currently signed-in user's identity info.
    Streamlit surfaces user data through st.user.
    """
    if not st.user.is_logged_in:
        return None

    email = str(getattr(st.user, "email", "") or "").strip().lower()
    name = str(getattr(st.user, "name", "") or "").strip()

    if not email:
        return None

    if not name:
        name = email.split("@")[0]

    return {
        "user_id": email,   # stable enough for now; later can map to UUID if desired
        "email": email,
        "display_name": name,
    }


def get_or_create_current_user():
    """
    Ensure the logged-in user exists in the users worksheet.
    Returns a dict with user_id, email, display_name.
    """
    identity = get_logged_in_identity()
    if identity is None:
        return None

    users_df = load_users_sheet()

    existing = users_df[users_df["user_id"].astype(str).str.lower() == identity["user_id"]]
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
# Read/write the logged-in user's fragrance collection
# from the "collections" worksheet.
# =========================================================
@st.cache_data(ttl=0, show_spinner=False)
def load_collections_sheet() -> pd.DataFrame:
    """Read the collections worksheet and normalize its columns."""
    try:
        conn = get_gsheets_conn()
        df = conn.read(worksheet="collections", ttl=0)
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
    conn.update(worksheet="collections", data=collections_df)
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

    # Prefer saved fragrance_name if present
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
    """Load the user's saved collection into session state once per session."""
    loaded = load_user_collection(user_id)
    st.session_state.my_collection = loaded
    
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

            .small-note {{
                color: {theme['muted']};
                font-size: 0.86rem;
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
    """Fallback Amazon affiliate search."""
    return f"https://www.amazon.com/s?k={urllib.parse.quote_plus(query)}&tag={AFFILIATE_TAG}"


# =========================================================
# COMBO ENGINE
# =========================================================
def combo_score(a, b, vibe, profile, intensity, mixing_style) -> float:
    """
    Score a combo based on note overlap, bridge notes, plausibility,
    vibe/profile alignment, intensity, and brand relationship.
    """
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
        if same_brand:
            score += 2.0
        else:
            score -= 1.5

    elif mixing_style == "Cross-House":
        if not same_brand:
            score += 2.0
        else:
            score -= 1.5

    elif mixing_style == "Balanced":
        if same_brand:
            score += 0.5
        else:
            score += 0.8

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

    page = st.radio(
        "Go to",
        valid_pages,
        index=valid_pages.index(current_page),
    )
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()

    st.divider()
    st.caption("As an Amazon Associate I earn from qualifying purchases.")

# =========================================================
# APP HEADER
# =========================================================
st.markdown('<div class="main-title">🧪 SniffLab</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Pick your mood, tap Sniff, get layering ideas.</div>', unsafe_allow_html=True)
st.markdown('<div class="hint-box">On mobile, tap <b>››</b> in the top-left corner to open the menu.</div>', unsafe_allow_html=True)

# =========================================================
# LOGIN GATE
# Users must sign in with Google before we load or save
# anything tied to their identity.
# =========================================================
if not st.user.is_logged_in:
    st.markdown("### Sign in")
    st.markdown(
        """
        <div class="hero-box">
        <b>Save your collection</b><br><br>
        Sign in with Google so SniffLab can keep your collection,
        wishlist, saved combos, and ratings attached to you.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Log in with Google", type="primary"):
        st.login()

    st.stop()

# User is logged in from here forward
current_user = get_or_create_current_user()

# Load this user's saved collection from Google Sheets
if "collection_loaded_for_user" not in st.session_state:
    st.session_state.collection_loaded_for_user = ""

if st.session_state.collection_loaded_for_user != current_user["user_id"]:
    sync_session_collection_from_cloud(current_user["user_id"])
    st.session_state.collection_loaded_for_user = current_user["user_id"]

top1, top2 = st.columns([4, 1])
with top1:
    st.caption(f"Signed in as: {current_user['display_name']}")
with top2:
    if st.button("Log out"):
        st.logout()

if st.session_state.last_added:
    st.toast(f"Added: {st.session_state.last_added}")
    st.session_state.last_added = ""

# =========================================================
# PAGE: HOME
# Landing page = Sniff only
# =========================================================
if st.session_state.page == "Home":
    st.markdown("### Sniff")

    st.markdown(
        f"""
        <div class="hero-box">
        <b>Your Collection</b><br>
        {len(st.session_state.my_collection)} fragrance(s) ready to layer
        </div>
        """,
        unsafe_allow_html=True,
    )

    source_mode = st.segmented_control(
        "Where should Sniff pull from?",
        ["My Collection", "Collection + Community"],
        selection_mode="single",
        default=st.session_state.source_mode,
    )
    st.session_state.source_mode = source_mode

    c1, c2 = st.columns(2)

    with c1:
        vibe = st.selectbox(
            "How are you feeling?",
            ["Any", "Sexy", "Clean", "Cozy", "Night Out", "Soft"],
            index=["Any", "Sexy", "Clean", "Cozy", "Night Out", "Soft"].index(st.session_state.vibe),
        )
        st.session_state.vibe = vibe

    with c2:
        profile = st.selectbox(
            "What scent profile do you want?",
            ["Any", "Gourmand", "Floral", "Fresh", "Woody", "Fruity"],
            index=["Any", "Gourmand", "Floral", "Fresh", "Woody", "Fruity"].index(st.session_state.profile),
        )
        st.session_state.profile = profile

    c3, c4 = st.columns(2)

    with c3:
        intensity = st.selectbox(
            "How strong should it feel?",
            ["Easy", "Signature", "Beast Mode", "Experimental"],
            index=["Easy", "Signature", "Beast Mode", "Experimental"].index(st.session_state.intensity),
        )
        st.session_state.intensity = intensity

    with c4:
        mixing_style = st.selectbox(
            "What kind of mixing do you want?",
            ["Balanced", "Same House", "Cross-House"],
            index=["Balanced", "Same House", "Cross-House"].index(st.session_state.mixing_style),
        )
        st.session_state.mixing_style = mixing_style

    st.caption("Choose your mood and style, then tap Sniff.")

    if st.button("🧪 Sniff", type="primary"):
        with st.spinner("Sniffing your collection and building layering ideas..."):
            collection_df = df[df["display_name"].isin(st.session_state.my_collection)].copy()

            if collection_df.empty:
                st.warning("Add at least one fragrance to your collection first.")
            else:
                pool_df = collection_df.copy() if source_mode == "My Collection" else df.copy()

                results = []
                seen = set()

                for _, a in collection_df.iterrows():
                    for _, b in pool_df.iterrows():
                        if a["display_name"] == b["display_name"]:
                            continue

                        key = tuple(sorted([a["display_name"], b["display_name"]]))
                        if key in seen:
                            continue
                        seen.add(key)

                        score = combo_score(a, b, vibe, profile, intensity, mixing_style)
                        tier = combo_tier(score, intensity)

                        results.append({
                            "a": a,
                            "b": b,
                            "score": score,
                            "tier": tier,
                            "combo_name": combo_name(a, b, tier),
                            "description": combo_description(a, b, vibe, profile),
                            "key": f"{key[0]}|||{key[1]}",
                        })

                results = sorted(results, key=lambda x: x["score"], reverse=True)

                if mixing_style == "Balanced":
                    same_house = []
                    cross_house = []

                    for combo in results:
                        brand_a = str(combo["a"]["brand"]).strip().lower()
                        brand_b = str(combo["b"]["brand"]).strip().lower()

                        if brand_a == brand_b:
                            same_house.append(combo)
                        else:
                            cross_house.append(combo)

                    mixed_results = []
                    max_len = max(len(same_house), len(cross_house))

                    for i in range(max_len):
                        if i < len(cross_house):
                            mixed_results.append(cross_house[i])
                        if i < len(same_house):
                            mixed_results.append(same_house[i])

                    st.session_state.latest_combos = mixed_results[:12]
                else:
                    st.session_state.latest_combos = results[:12]

    if st.session_state.latest_combos:
        st.markdown("### Your Layering Suggestions")

        for combo in st.session_state.latest_combos:
            a = combo["a"]
            b = combo["b"]
            combo_key = combo["key"]
            saved_rating = st.session_state.combo_ratings.get(combo_key, "unreviewed")
            same_house = str(a["brand"]).strip().lower() == str(b["brand"]).strip().lower()

            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="tier-chip">{combo["tier"]}</div>', unsafe_allow_html=True)
            st.caption("Same House" if same_house else "Cross-House")
            st.markdown(f'<div class="sniff-name">{combo["combo_name"]}</div>', unsafe_allow_html=True)
            st.write(f"**Layer:** {a['display_name']} + {b['display_name']}")
            st.write(f"**Why it may work:** {combo['description']}")
            st.write(f"**Score:** {combo['score']}")
            st.write(f"**Current rating:** {saved_rating.title() if saved_rating != 'unreviewed' else 'Unreviewed'}")
            st.caption("Suggested use: 2 sprays of the richer scent on chest, 1 spray of the brighter scent on neck or shirt.")

            r1, r2, r3, r4, r5, r6 = st.columns(6)

            if r1.button("🚀", key=f"amazing_{combo_key}"):
                st.session_state.combo_ratings[combo_key] = "amazing"
                st.rerun()

            if r2.button("👌", key=f"good_{combo_key}"):
                st.session_state.combo_ratings[combo_key] = "good"
                st.rerun()

            if r3.button("😐", key=f"neutral_{combo_key}"):
                st.session_state.combo_ratings[combo_key] = "neutral"
                st.rerun()

            if r4.button("🤢", key=f"barf_{combo_key}"):
                st.session_state.combo_ratings[combo_key] = "barf"
                st.rerun()

            if r5.button("⭐", key=f"save_combo_{combo_key}"):
                combo_label = f"{combo['combo_name']} | {a['display_name']} + {b['display_name']}"
                if combo_label not in st.session_state.saved_combos:
                    st.session_state.saved_combos.append(combo_label)
                st.rerun()

            r6.link_button("🛒", amazon_search_link(f"{b['brand_pretty']} {b['name_pretty']}"))
            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGE: BROWSE
# Add fragrances to collection
# =========================================================
elif st.session_state.page == "Browse":
    st.markdown("### Add Fragrances")

    quick1, quick2, quick3 = st.columns(3)
    if quick1.button("Desmirage"):
        st.session_state.search_query = "desmirage"
        st.session_state.brand_filter = "All Brands"
        st.rerun()
    if quick2.button("Arlyn"):
        st.session_state.search_query = "arlyn"
        st.session_state.brand_filter = "All Brands"
        st.rerun()
    if quick3.button("Jean Rish"):
        st.session_state.search_query = "jean rish"
        st.session_state.brand_filter = "All Brands"
        st.rerun()

    f1, f2 = st.columns([1, 2])
    all_brands = sorted(df["brand_pretty"].dropna().unique().tolist())

    with f1:
        options = ["All Brands"] + all_brands
        brand_filter = st.selectbox(
            "Brand",
            options,
            index=options.index(st.session_state.brand_filter) if st.session_state.brand_filter in options else 0,
        )
        st.session_state.brand_filter = brand_filter

    with f2:
        search_query = st.text_input(
            "Search",
            value=st.session_state.search_query,
            placeholder="Try desmirage, vanilla, cherry, floral...",
        )
        st.session_state.search_query = search_query

    filtered_df = df.copy()

    if brand_filter != "All Brands":
        filtered_df = filtered_df[filtered_df["brand_pretty"] == brand_filter]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[filtered_df["search_text"].str.contains(q, na=False)]

    filtered_df = filtered_df[~filtered_df["display_name"].isin(st.session_state.my_collection)].copy()
    filtered_df["brand_priority"] = filtered_df["brand"].str.lower().apply(lambda x: 0 if x == "desmirage" else 1)
    filtered_df = filtered_df.sort_values(
        ["brand_priority", "brand_pretty", "name_pretty"],
        ascending=[True, True, True],
    )

    results_df = filtered_df.head(30)

    bulk1, bulk2 = st.columns(2)
    if bulk1.button("➕ Add Selected"):
        added_any = False
        selected_rows = results_df[results_df["display_name"].isin(st.session_state.browse_selected)].copy()

        for _, row in selected_rows.iterrows():
            add_collection_item(current_user["user_id"], row)
            if row["display_name"] not in st.session_state.my_collection:
                st.session_state.my_collection.append(row["display_name"])
                added_any = True

        st.session_state.browse_selected = []
        if added_any:
            st.session_state.last_added = "Selected fragrances"
        st.rerun()

    if bulk2.button("Clear Selection"):
        st.session_state.browse_selected = []
        st.rerun()

    if results_df.empty:
        st.info("No fragrances matched your search.")
    else:
        st.caption(f"Showing {len(results_df)} result(s)")

        for _, row in results_df.iterrows():
            accords = [x for x in [
                row["mainaccord1"],
                row["mainaccord2"],
                row["mainaccord3"],
                row["mainaccord4"],
                row["mainaccord5"],
            ] if x]

            top_notes = ", ".join(row["top_list"][:5]) if row["top_list"] else "—"
            middle_notes = ", ".join(row["middle_list"][:5]) if row["middle_list"] else "—"
            base_notes = ", ".join(row["base_list"][:5]) if row["base_list"] else "—"
            accord_text = " • ".join(accords[:4]) if accords else "—"

            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)

            selected = st.checkbox(
                f"Select {row['display_name']}",
                value=row["display_name"] in st.session_state.browse_selected,
                key=f"browse_select_{row['id']}",
                label_visibility="collapsed",
            )

            if selected and row["display_name"] not in st.session_state.browse_selected:
                st.session_state.browse_selected.append(row["display_name"])
            elif not selected and row["display_name"] in st.session_state.browse_selected:
                st.session_state.browse_selected.remove(row["display_name"])

            st.markdown(
                f'<div class="sniff-name">{family_icon(row["family"])} {row["name_pretty"]} '
                f'<span class="sniff-meta">| {row["brand_pretty"]}</span></div>',
                unsafe_allow_html=True,
            )

            if row["inspired_by"]:
                st.markdown(
                    f'<div><span class="mini-label">Inspired By</span><br>{row["inspired_by"]}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f'<div style="margin-top:8px;"><span class="mini-label">Profile</span><br>{row["family"]} | {accord_text}</div>',
                unsafe_allow_html=True,
            )

            b1, b2, b3 = st.columns(3)

            if b1.button("➕", key=f"add_{row['id']}"):
                add_collection_item(current_user["user_id"], row)
                if row["display_name"] not in st.session_state.my_collection:
                    st.session_state.my_collection.append(row["display_name"])
                st.session_state.last_added = row["display_name"]
                st.rerun()

            if b2.button("⭐", key=f"save_frag_{row['id']}"):
                if row["display_name"] not in st.session_state.sniff_list:
                    st.session_state.sniff_list.append(row["display_name"])
                st.rerun()

            b3.link_button("🛒", amazon_search_link(f"{row['brand_pretty']} {row['name_pretty']}"))

            with st.expander("More details"):
                st.markdown(f"**Top Notes**  \n{top_notes}")
                st.markdown(f"**Middle Notes**  \n{middle_notes}")
                st.markdown(f"**Base Notes**  \n{base_notes}")

            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGE: COLLECTION
# =========================================================
elif st.session_state.page == "Collection":
    st.markdown("### My Collection")

    top1, top2 = st.columns(2)
    if top1.button("✕ Remove Selected"):
        for fragrance_name in st.session_state.collection_selected:
            remove_collection_item(current_user["user_id"], fragrance_name)

        st.session_state.my_collection = [
            x for x in st.session_state.my_collection
            if x not in st.session_state.collection_selected
        ]
        st.session_state.collection_selected = []
        st.rerun()

    if top2.button("Clear Selection", key="clear_collection_selection"):
        st.session_state.collection_selected = []
        st.rerun()

    if st.session_state.my_collection:
        collection_df = df[df["display_name"].isin(st.session_state.my_collection)].copy()

        for family in ["Gourmand", "Floral", "Fresh", "Woody / Warm", "Fruity", "Other"]:
            family_rows = collection_df[collection_df["family"] == family]
            if family_rows.empty:
                continue

            st.markdown(f"#### {family_icon(family)} {family}")

            for _, row in family_rows.sort_values("display_name").iterrows():
                st.markdown('<div class="collection-chip">', unsafe_allow_html=True)

                selected = st.checkbox(
                    f"Select {row['display_name']}",
                    value=row["display_name"] in st.session_state.collection_selected,
                    key=f"collection_select_{row['display_name']}",
                    label_visibility="collapsed",
                )

                if selected and row["display_name"] not in st.session_state.collection_selected:
                    st.session_state.collection_selected.append(row["display_name"])
                elif not selected and row["display_name"] in st.session_state.collection_selected:
                    st.session_state.collection_selected.remove(row["display_name"])

                c1, c2 = st.columns([6, 1])
                c1.markdown(f"**{row['display_name']}**")
                if c2.button("✕", key=f"remove_{row['display_name']}"):
                    remove_collection_item(current_user["user_id"], row["display_name"])
                    st.session_state.my_collection = [
                        x for x in st.session_state.my_collection if x != row["display_name"]
                    ]
                    if row["display_name"] in st.session_state.collection_selected:
                        st.session_state.collection_selected.remove(row["display_name"])
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Your collection is empty.")

# =========================================================
# PAGE: SAVED
# =========================================================
elif st.session_state.page == "Saved":
    st.markdown("### Saved")

    st.markdown("#### ⭐ Saved Fragrances")
    if st.session_state.sniff_list:
        for item in st.session_state.sniff_list:
            c1, c2 = st.columns([6, 1])
            c1.markdown(f'<div class="collection-chip"><b>{item}</b></div>', unsafe_allow_html=True)
            if c2.button("✕", key=f"remove_saved_frag_{item}"):
                st.session_state.sniff_list = [x for x in st.session_state.sniff_list if x != item]
                st.rerun()
    else:
        st.caption("Nothing saved yet.")

    st.markdown("#### 🧪 Saved Combos")
    if st.session_state.saved_combos:
        for combo in st.session_state.saved_combos:
            c1, c2 = st.columns([6, 1])
            c1.markdown(f'<div class="collection-chip"><b>{combo}</b></div>', unsafe_allow_html=True)
            if c2.button("✕", key=f"remove_saved_combo_{combo}"):
                st.session_state.saved_combos = [x for x in st.session_state.saved_combos if x != combo]
                st.rerun()
    else:
        st.caption("No saved combos yet.")

# =========================================================
# PAGE: HELP
# =========================================================
elif st.session_state.page == "Help":
    st.markdown("### Help")

    st.markdown(
        """
        <div class="hero-box">
        <b>How SniffLab works</b><br><br>
        1. Open <b>Browse</b>.<br>
        2. Add the fragrances you own to <b>My Collection</b>.<br>
        3. Go back to <b>Home</b>.<br>
        4. Pick your mood and scent style.<br>
        5. Tap <b>Sniff</b> to get layering ideas.<br><br>

        <b>What the buttons mean</b><br>
        ➕ Add to your collection<br>
        ⭐ Save for later<br>
        ✕ Remove<br>
        🛒 Check Amazon<br><br>

        <b>Mixing Style</b><br>
        Balanced = same brand and different brand ideas<br>
        Same House = mostly the same brand<br>
        Cross-House = mostly different brands
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# PAGE: SETTINGS
# Theme controls + Google Sheets connection test
# =========================================================
elif st.session_state.page == "Settings":
    st.markdown("### Settings")

    selected_theme = st.selectbox(
        "Theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme_name),
    )
    if selected_theme != st.session_state.theme_name:
        st.session_state.theme_name = selected_theme
        st.rerun()

    st.markdown(
        """
        <div class="hero-box">
        <b>Theme</b><br><br>
        Change the colors used in the app here.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Google Sheets Connection Test")
    st.caption("Use this to confirm SniffLab can talk to your private Google Sheet before we turn on saving collections.")

    if st.button("Test Google Sheets Connection"):
        try:
            conn = get_gsheets_conn()
            test_df = conn.read(worksheet="users", ttl=0)
            st.success(f"Connected successfully. Found {len(test_df)} row(s) in the users tab.")
        except Exception as e:
            st.error(f"Connection failed: {e}")

    st.markdown(
        """
        <div class="hero-box">
        <b>What happens next</b><br><br>
        Once this connection test works, the next step will be saving and loading each user's collection so it is not lost on refresh.
        </div>
        """,
        unsafe_allow_html=True,
    )