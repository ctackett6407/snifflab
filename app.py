import streamlit as st
import pandas as pd
import urllib.parse
import random

# =========================================================
# SNIFFLAB CONFIG
# =========================================================
CSV_PATH = "data/fragrances_master.csv"
AFFILIATE_TAG = "christacket04-20"

st.set_page_config(
    page_title="SniffLab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# THEME PRESETS
# =========================================================
# These themes now control page/card/text styling only.
# Buttons are left to Streamlit's native theme system.
THEMES = {
    "System Default": None,
    "Midnight": {
        "bg": "#050816",
        "card": "#111827",
        "text": "#F9FAFB",
        "muted": "#9CA3AF",
        "accent": "#8B5CF6",
        "border": "#374151",
        "sidebar_bg": "#0B1020",
    },
    "Monochrome": {
        "bg": "#111111",
        "card": "#1F1F1F",
        "text": "#F5F5F5",
        "muted": "#BDBDBD",
        "accent": "#E5E7EB",
        "border": "#444444",
        "sidebar_bg": "#191919",
    },
    "Pink Pretty": {
        "bg": "#FFF5FB",
        "card": "#FFE0F1",
        "text": "#4A1030",
        "muted": "#9C4A76",
        "accent": "#FF2DAA",
        "border": "#F39ACB",
        "sidebar_bg": "#FFD9EE",
    },
    "Rainbow Pop": {
        "bg": "#FFF8FF",
        "card": "#FFF0FB",
        "text": "#2A1540",
        "muted": "#7A5A9A",
        "accent": "#FF4FD8",
        "border": "#9B5CFF",
        "sidebar_bg": "#FFE8FF",
    },
}

# =========================================================
# SESSION STATE DEFAULTS
# =========================================================
if "theme_name" not in st.session_state:
    st.session_state.theme_name = "System Default"

if "page" not in st.session_state:
    st.session_state.page = "Home"

# Store collection by stable fragrance id
if "my_collection_ids" not in st.session_state:
    st.session_state.my_collection_ids = []

# Store saved combo keys
if "saved_combo_keys" not in st.session_state:
    st.session_state.saved_combo_keys = []

if "combo_ratings" not in st.session_state:
    st.session_state.combo_ratings = {}

if "last_added" not in st.session_state:
    st.session_state.last_added = ""

if "latest_combos" not in st.session_state:
    st.session_state.latest_combos = []

if "brand_filter" not in st.session_state:
    st.session_state.brand_filter = "All Brands"

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "sniff_mode" not in st.session_state:
    st.session_state.sniff_mode = "My Collection Only"

if "mood" not in st.session_state:
    st.session_state.mood = "Any"

if "layer_count" not in st.session_state:
    st.session_state.layer_count = 2

if "spray_style" not in st.session_state:
    st.session_state.spray_style = "Moderate"

if "vibe" not in st.session_state:
    st.session_state.vibe = "Any"

theme = THEMES[st.session_state.theme_name]

# =========================================================
# GLOBAL APP STYLING
# =========================================================
# Buttons are intentionally NOT custom styled here.
# We let Streamlit handle button contrast natively.
if theme is not None:
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {theme['bg']};
            color: {theme['text']};
        }}

        html, body, [class*="css"] {{
            color: {theme['text']};
        }}

        .block-container {{
            padding-top: 0.8rem;
            padding-bottom: 4rem;
        }}

        .main-title {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
            color: {theme['text']};
        }}

        .sub-title {{
            font-size: 1rem;
            color: {theme['muted']};
            margin-bottom: 0.8rem;
        }}

        .hint-box {{
            background: {theme['card']};
            border: 1px solid {theme['border']};
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 12px;
            color: {theme['muted']};
            font-size: 0.95rem;
        }}

        .sniff-card {{
            background: {theme['card']};
            border: 1px solid {theme['border']};
            border-radius: 18px;
            padding: 14px;
            margin-bottom: 12px;
        }}

        .sniff-name {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {theme['text']};
            margin-bottom: 0.15rem;
        }}

        .sniff-meta {{
            color: {theme['muted']};
            font-size: 0.92rem;
            margin-bottom: 0.3rem;
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
            color: {theme['text']};
        }}

        .hero-box {{
            background: {theme['card']};
            border: 1px solid {theme['border']};
            border-radius: 20px;
            padding: 16px;
            margin-bottom: 14px;
            color: {theme['text']};
        }}

        .small-note {{
            color: {theme['muted']};
            font-size: 0.86rem;
        }}

        .combo-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            background: {theme['bg']};
            border: 1px solid {theme['border']};
            color: {theme['text']};
            font-size: 0.78rem;
            margin-right: 6px;
            margin-bottom: 6px;
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

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {{
            color: {theme['text']} !important;
            -webkit-text-fill-color: {theme['text']} !important;
        }}

        section[data-testid="stSidebar"] {{
            background: {theme['sidebar_bg']};
            border-right: 1px solid {theme['border']};
        }}
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# DATA HELPERS
# =========================================================
@st.cache_data
def load_fragrances():
    """
    Load the master fragrance catalog and create friendly
    search/display columns used throughout the app.
    """
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

    def pretty_text(value: str) -> str:
        value = str(value).replace("-", " ").replace("_", " ").strip()
        return " ".join(word.capitalize() for word in value.split())

    def split_notes(value: str):
        if not value:
            return []
        return [x.strip() for x in str(value).split(";") if x.strip()]

    def clean_accord(value: str) -> str:
        return str(value).replace(",", " ").strip().lower()

    def infer_family(row):
        text = " ".join([
            str(row.get("mainaccord1", "")),
            str(row.get("mainaccord2", "")),
            str(row.get("mainaccord3", "")),
            str(row.get("mainaccord4", "")),
            str(row.get("mainaccord5", "")),
            str(row.get("top_notes", "")),
            str(row.get("middle_notes", "")),
            str(row.get("base_notes", "")),
        ]).lower()

        if any(x in text for x in ["gourmand", "sweet", "vanilla", "dessert", "marzipan", "milky", "caramel", "chocolate", "praline"]):
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

    # Friendly display columns
    df["name_pretty"] = df["name"].apply(pretty_text)
    df["brand_pretty"] = df["brand"].apply(pretty_text)
    df["display_name"] = df["name_pretty"] + " — " + df["brand_pretty"]

    # Search blob
    search_cols = [
        "name", "brand", "inspired_by", "top_notes", "middle_notes",
        "base_notes", "mainaccord1", "mainaccord2", "mainaccord3",
        "mainaccord4", "mainaccord5"
    ]
    for col in search_cols:
        if col not in df.columns:
            df[col] = ""

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

    # Notes
    df["top_list"] = df["top_notes"].apply(split_notes)
    df["middle_list"] = df["middle_notes"].apply(split_notes)
    df["base_list"] = df["base_notes"].apply(split_notes)

    # Accords
    df["accords"] = df[
        ["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]
    ].apply(
        lambda row: [clean_accord(x) for x in row.tolist() if str(x).strip()],
        axis=1
    )

    # Flatten notes
    df["all_notes"] = df.apply(
        lambda row: list(dict.fromkeys(row["top_list"] + row["middle_list"] + row["base_list"])),
        axis=1
    )

    df["family"] = df.apply(infer_family, axis=1)
    return df


def amazon_search_link(query: str) -> str:
    """Build Amazon affiliate search link."""
    return f"https://www.amazon.com/s?k={urllib.parse.quote_plus(query)}&tag={AFFILIATE_TAG}"


def family_icon(family):
    """Emoji label for collection grouping."""
    return {
        "Gourmand": "🧁",
        "Floral": "🌸",
        "Fresh": "🍋",
        "Woody / Warm": "🪵",
        "Fruity": "🍒",
        "Other": "🧪"
    }.get(family, "🧪")


def get_collection_df(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["id"].isin(st.session_state.my_collection_ids)].copy()


def note_set(row):
    return set([x.lower().strip() for x in row["all_notes"] if str(x).strip()])


def accord_set(row):
    return set([x.lower().strip() for x in row["accords"] if str(x).strip()])


def fragrance_role(row):
    """
    Assign a rough role to a fragrance in a layering stack.
    """
    accords = accord_set(row)
    notes = note_set(row)
    text = " ".join(list(accords | notes))

    if any(x in text for x in ["citrus", "bergamot", "lemon", "grapefruit", "marine", "mint", "fresh", "aquatic"]):
        return "Lift"
    if any(x in text for x in ["rose", "jasmine", "orange blossom", "neroli", "iris", "floral", "fruity", "pear", "peach", "cherry", "lychee"]):
        return "Heart"
    if any(x in text for x in ["amber", "vanilla", "musk", "woody", "oud", "tobacco", "sandalwood", "patchouli", "sweet", "gourmand"]):
        return "Anchor"
    return "Support"


def layering_style_summary(rows):
    """
    Determine the overall vibe family of a combo.
    """
    all_accords = set().union(*[accord_set(r) for r in rows]) if rows else set()
    all_notes = set().union(*[note_set(r) for r in rows]) if rows else set()
    text = " ".join(list(all_accords) + list(all_notes))

    if any(x in text for x in ["gourmand", "vanilla", "caramel", "sweet", "dessert", "chocolate", "praline"]):
        return "Sweet"
    if any(x in text for x in ["fresh", "marine", "citrus", "bergamot", "mint", "aquatic"]):
        return "Fresh"
    if any(x in text for x in ["rose", "jasmine", "orange blossom", "neroli", "floral", "iris"]):
        return "Floral"
    if any(x in text for x in ["amber", "woody", "tobacco", "sandalwood", "patchouli", "oud"]):
        return "Warm"
    if any(x in text for x in ["pear", "peach", "cherry", "lychee", "mango", "fruity"]):
        return "Fruity"
    return "Balanced"


def combo_score_rows(rows, vibe="Any", spray_style="Moderate"):
    """
    Smarter score for 2 or 3 fragrance combinations.
    """
    all_accords = [accord_set(r) for r in rows]
    all_notes = [note_set(r) for r in rows]

    score = 0.0

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            shared_accords = all_accords[i] & all_accords[j]
            shared_notes = all_notes[i] & all_notes[j]
            score += len(shared_accords) * 3.0
            score += len(shared_notes) * 1.25

    combined_text = " ".join(
        list(set().union(*all_accords)) +
        list(set().union(*all_notes))
    )

    synergy_rules = [
        (["vanilla", "amber"], 2.5),
        (["musk", "floral"], 2.0),
        (["citrus", "woody"], 2.0),
        (["fresh", "amber"], 1.4),
        (["cherry", "vanilla"], 2.2),
        (["coffee", "vanilla"], 2.0),
        (["tobacco", "vanilla"], 2.3),
        (["rose", "musk"], 1.8),
        (["pear", "floral"], 1.4),
        (["gourmand", "musk"], 1.7),
    ]
    for needed, pts in synergy_rules:
        if all(n in combined_text for n in needed):
            score += pts

    roles = [fragrance_role(r) for r in rows]
    if "Lift" in roles:
        score += 1.2
    if "Heart" in roles:
        score += 1.2
    if "Anchor" in roles:
        score += 1.5
    if len(set(roles)) >= 2:
        score += 1.0

    clash_rules = [
        (["marine", "tobacco"], 2.0),
        (["aquatic", "oud"], 2.2),
        (["green", "dessert"], 1.5),
        (["powdery", "marine"], 1.4),
    ]
    for bad_pair, penalty in clash_rules:
        if all(n in combined_text for n in bad_pair):
            score -= penalty

    dense_terms = ["oud", "tobacco", "amber", "vanilla", "sweet", "gourmand", "patchouli"]
    dense_count = sum(1 for term in dense_terms if term in combined_text)
    if len(rows) == 3 and dense_count >= 5:
        score -= 1.5

    vibe_map = {
        "Any": [],
        "Sweet": ["sweet", "vanilla", "gourmand", "praline", "caramel"],
        "Fresh": ["fresh", "citrus", "marine", "mint", "bergamot"],
        "Date Night": ["amber", "musk", "vanilla", "tobacco", "rose"],
        "Loud": ["amber", "woody", "oud", "sweet", "tobacco"],
        "Soft": ["musk", "floral", "powdery", "clean"],
        "Cozy": ["vanilla", "amber", "musk", "cashmere", "sweet"],
        "Clean": ["fresh", "citrus", "soap", "musk", "white floral"],
        "Expensive": ["woody", "amber", "iris", "musk", "sandalwood", "rose"],
    }
    for term in vibe_map.get(vibe, []):
        if term in combined_text:
            score += 0.8

    if spray_style == "Oversprayer":
        risky_terms = ["oud", "tobacco", "patchouli", "leather", "animalic", "smoky"]
        risky_hits = sum(1 for term in risky_terms if term in combined_text)
        score -= risky_hits * 0.5
    elif spray_style == "Conservative":
        airy_terms = ["fresh", "citrus", "marine", "musk"]
        airy_hits = sum(1 for term in airy_terms if term in combined_text)
        score += airy_hits * 0.2

    return round(score, 2)


def combo_name_rows(rows, vibe="Any"):
    """
    More creative combo naming.
    """
    style = layering_style_summary(rows)

    name_bank = {
        "Sweet": [
            "Sugar Veil", "Velvet Crave", "Dessert Heat", "Frosted Skin", "Candy Smoke"
        ],
        "Fresh": [
            "Clean Halo", "Blue Static", "Citrus Rush", "Air Charge", "White Pulse"
        ],
        "Floral": [
            "Petal Drift", "Blush Bloom", "Silk Garden", "Soft Bloom", "Rose Signal"
        ],
        "Warm": [
            "Ember Silk", "Amber Voltage", "Midnight Burn", "Velvet Heat", "Golden Smoke"
        ],
        "Fruity": [
            "Neon Fruit", "Juicy Signal", "Cherry Current", "Sun Pop", "Gloss Rush"
        ],
        "Balanced": [
            "After Velvet", "Layer Theory", "Soft Static", "Private Blend", "Skin Echo"
        ],
    }

    if vibe == "Date Night":
        return random.choice(["After Hours", "Velvet After Dark", "Midnight Pull", "Skin Chemistry"])
    if vibe == "Expensive":
        return random.choice(["Private Reserve", "Gold Room", "Black Tie Glow", "Cashmere Signal"])

    return random.choice(name_bank.get(style, name_bank["Balanced"]))


def combo_description_rows(rows):
    """
    Explain why the combo works in a more interesting way.
    """
    roles = [(r["display_name"], fragrance_role(r)) for r in rows]
    role_lines = []

    for name, role in roles:
        if role == "Lift":
            role_lines.append(f"{name} adds brightness and lift.")
        elif role == "Heart":
            role_lines.append(f"{name} adds body and character through the middle.")
        elif role == "Anchor":
            role_lines.append(f"{name} gives the combo depth and staying power.")
        else:
            role_lines.append(f"{name} supports the blend without overpowering it.")

    style = layering_style_summary(rows)
    opening = {
        "Sweet": "This stack leans creamy, addictive, and easy to notice.",
        "Fresh": "This stack feels airy, bright, and wearable.",
        "Floral": "This stack feels smooth, soft, and expressive.",
        "Warm": "This stack leans rich, deep, and confident.",
        "Fruity": "This stack feels playful and energetic with extra pop.",
        "Balanced": "This stack is balanced and rounded with a smooth transition.",
    }.get(style, "This stack feels balanced and wearable.")

    return opening + " " + " ".join(role_lines)


def spray_guide(rows, spray_style="Moderate"):
    """
    Give placement guidance based on combo density and user spray style.
    """
    combined_text = " ".join(
        list(set().union(*[accord_set(r) for r in rows])) +
        list(set().union(*[note_set(r) for r in rows]))
    )

    is_dense = any(x in combined_text for x in ["oud", "tobacco", "amber", "patchouli", "leather", "gourmand", "sweet"])
    is_fresh = any(x in combined_text for x in ["fresh", "citrus", "marine", "mint", "aquatic"])

    if spray_style == "Conservative":
        if is_dense:
            return "1 spray on chest, 1 on lower neck. Skip extra fabric sprays so the blend stays smooth."
        if is_fresh:
            return "1 on chest, 1 on neck, optional 1 on shirt for a light scent trail."
        return "1 on chest, 1 on neck, optional 1 on shirt."

    if spray_style == "Oversprayer":
        if is_dense:
            return "2 on chest, 1 back of neck, 1 shirt. Keep heavy notes off the front neck so it stays strong without getting thick."
        if is_fresh:
            return "2 on chest, 1 back of neck, 1 each side of neck, 2 on shirt. Fresh blends can handle more fabric and air."
        return "2 on chest, 1 back of neck, 1 each side of neck, 1 shirt, optional 1 forearm."

    if is_dense:
        return "2 on chest, 1 on lower neck, optional 1 back of neck. This keeps depth without overloading the air."
    if is_fresh:
        return "2 on chest, 1 on neck, 1 shirt. Fresh blends open nicely with one fabric spray."
    return "2 on chest, 1 on neck, 1 shirt for a balanced cloud."


def build_combo_result(rows, vibe="Any", spray_style="Moderate"):
    return {
        "rows": rows,
        "score": combo_score_rows(rows, vibe=vibe, spray_style=spray_style),
        "combo_name": combo_name_rows(rows, vibe=vibe),
        "description": combo_description_rows(rows),
        "spray_guide": spray_guide(rows, spray_style=spray_style),
        "style": layering_style_summary(rows),
        "key": "|||".join(sorted([r["display_name"] for r in rows]))
    }


# =========================================================
# LOAD DATA
# =========================================================
df = load_fragrances()

# =========================================================
# SIDEBAR MENU
# =========================================================
with st.sidebar:
    st.header("SniffLab")
    st.caption("Use the menu below")

    page = st.radio(
        "Go to",
        ["Home", "Browse", "Collection", "Sniff", "Saved"],
        index=["Home", "Browse", "Collection", "Sniff", "Saved"].index(st.session_state.page)
    )
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()

    st.divider()

    selected_theme = st.selectbox(
        "Theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme_name)
    )
    if selected_theme != st.session_state.theme_name:
        st.session_state.theme_name = selected_theme
        st.rerun()

    st.divider()
    st.caption("As an Amazon Associate I earn from qualifying purchases.")

# =========================================================
# TOP HEADER
# =========================================================
st.markdown('<div class="main-title">🧪 SniffLab</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Fragrance layering made simple.</div>', unsafe_allow_html=True)

if st.session_state.last_added:
    st.toast(f"Added: {st.session_state.last_added}")
    st.session_state.last_added = ""

st.markdown(
    '<div class="hint-box">On mobile, tap <b>››</b> in the top-left corner anytime to open the menu.</div>',
    unsafe_allow_html=True
)

# =========================================================
# PAGE: HOME
# =========================================================
if st.session_state.page == "Home":
    st.markdown("### Welcome")
    st.markdown("""
    <div class="hero-box">
    <b>How SniffLab works</b><br><br>
    1. Open <b>Browse</b> and find your fragrances.<br>
    2. Tap <b>➕</b> to add them to your collection.<br>
    3. Open <b>Sniff</b> to get layering ideas.<br>
    4. Use <b>Save</b> to keep combos for later.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Browse Fragrances", use_container_width=True):
            st.session_state.page = "Browse"
            st.rerun()
    with c2:
        if st.button("Open My Collection", use_container_width=True):
            st.session_state.page = "Collection"
            st.rerun()

    st.caption("➕ Add  •  Save combos  •  ✕ Remove  •  🛒 Check price")

# =========================================================
# PAGE: BROWSE
# =========================================================
elif st.session_state.page == "Browse":
    st.markdown("### Browse Fragrances")

    quick1, quick2, quick3 = st.columns(3)
    with quick1:
        if st.button("Desmirage", use_container_width=True):
            st.session_state.search_query = "desmirage"
            st.session_state.brand_filter = "All Brands"
            st.rerun()
    with quick2:
        if st.button("Arlyn", use_container_width=True):
            st.session_state.search_query = "arlyn"
            st.session_state.brand_filter = "All Brands"
            st.rerun()
    with quick3:
        if st.button("Jean Rish", use_container_width=True):
            st.session_state.search_query = "jean rish"
            st.session_state.brand_filter = "All Brands"
            st.rerun()

    filter_col1, filter_col2 = st.columns([1, 2])
    all_brands = sorted(df["brand_pretty"].dropna().unique().tolist())

    with filter_col1:
        options = ["All Brands"] + all_brands
        brand_filter = st.selectbox(
            "Brand",
            options,
            index=options.index(st.session_state.brand_filter) if st.session_state.brand_filter in options else 0
        )
        st.session_state.brand_filter = brand_filter

    with filter_col2:
        search_query = st.text_input(
            "Search",
            value=st.session_state.search_query,
            placeholder="Try desmirage, vanilla, cherry, floral..."
        )
        st.session_state.search_query = search_query

    filtered_df = df.copy()

    if brand_filter != "All Brands":
        filtered_df = filtered_df[filtered_df["brand_pretty"] == brand_filter]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[filtered_df["search_text"].str.contains(q, na=False)]

    # Hide anything already in collection
    filtered_df = filtered_df[~filtered_df["id"].isin(st.session_state.my_collection_ids)].copy()

    # Slight prioritization for Desmirage
    filtered_df["brand_priority"] = filtered_df["brand"].str.lower().apply(lambda x: 0 if x == "desmirage" else 1)
    filtered_df = filtered_df.sort_values(
        ["brand_priority", "brand_pretty", "name_pretty"],
        ascending=[True, True, True]
    )

    results_df = filtered_df.head(24)

    if results_df.empty:
        st.info("No fragrances matched your search.")
    else:
        st.caption(f"Showing {len(results_df)} result(s)")
        for _, row in results_df.iterrows():
            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="sniff-name">{row["name_pretty"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sniff-meta">{row["brand_pretty"]}</div>', unsafe_allow_html=True)

            if row["inspired_by"]:
                st.markdown(f'<div class="mini-label">Inspired by</div><div>{row["inspired_by"]}</div>', unsafe_allow_html=True)

            accord_text = ", ".join([x for x in row["accords"] if x])
            if accord_text:
                st.markdown(f'<div class="mini-label">Accords</div><div>{accord_text}</div>', unsafe_allow_html=True)

            b1, b2 = st.columns(2)

            with b1:
                if st.button("➕ Add", key=f"add_{row['id']}", use_container_width=True):
                    if row["id"] not in st.session_state.my_collection_ids:
                        st.session_state.my_collection_ids.append(row["id"])
                    st.session_state.last_added = row["display_name"]
                    st.rerun()

            with b2:
                st.link_button(
                    "🛒 Check Price",
                    amazon_search_link(row["name_pretty"]),
                    use_container_width=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGE: COLLECTION
# =========================================================
elif st.session_state.page == "Collection":
    st.markdown("### My Collection")

    collection_df = get_collection_df(df)

    if not collection_df.empty:
        for family in ["Gourmand", "Floral", "Fresh", "Woody / Warm", "Fruity", "Other"]:
            family_rows = collection_df[collection_df["family"] == family]
            if family_rows.empty:
                continue

            st.markdown(f"#### {family_icon(family)} {family}")
            for _, row in family_rows.sort_values("display_name").iterrows():
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f'<div class="collection-chip"><b>{row["display_name"]}</b></div>', unsafe_allow_html=True)
                with c2:
                    if st.button("✕", key=f"remove_{row['id']}", use_container_width=True):
                        st.session_state.my_collection_ids = [
                            x for x in st.session_state.my_collection_ids if x != row["id"]
                        ]
                        st.rerun()
    else:
        st.info("Your collection is empty.")

# =========================================================
# PAGE: SNIFF
# =========================================================
elif st.session_state.page == "Sniff":
    st.markdown("### Sniff")

    top1, top2 = st.columns(2)
    with top1:
        sniff_mode = st.radio(
            "Use",
            ["My Collection Only", "My Collection + Community Fragrances"],
            index=["My Collection Only", "My Collection + Community Fragrances"].index(st.session_state.sniff_mode)
        )
        st.session_state.sniff_mode = sniff_mode

    with top2:
        vibe = st.selectbox(
            "Vibe",
            ["Any", "Sweet", "Fresh", "Date Night", "Loud", "Soft", "Cozy", "Clean", "Expensive"],
            index=["Any", "Sweet", "Fresh", "Date Night", "Loud", "Soft", "Cozy", "Clean", "Expensive"].index(st.session_state.vibe)
        )
        st.session_state.vibe = vibe

    mid1, mid2 = st.columns(2)
    with mid1:
        layer_count = st.radio(
            "How many layers",
            [2, 3],
            index=[2, 3].index(st.session_state.layer_count),
            horizontal=True
        )
        st.session_state.layer_count = layer_count

    with mid2:
        spray_style = st.selectbox(
            "Spray style",
            ["Conservative", "Moderate", "Oversprayer"],
            index=["Conservative", "Moderate", "Oversprayer"].index(st.session_state.spray_style)
        )
        st.session_state.spray_style = spray_style

    st.caption("Generate fun layering ideas based on what you own and how you like to wear fragrance.")

    if st.button("Generate Layering Ideas", type="primary", use_container_width=True):
        collection_df = get_collection_df(df)

        if collection_df.empty:
            st.warning("Add at least one fragrance to My Collection first.")
        else:
            pool_df = collection_df.copy() if sniff_mode == "My Collection Only" else df.copy()
            results = []
            seen = set()

            collection_rows = [row for _, row in collection_df.iterrows()]
            pool_rows = [row for _, row in pool_df.iterrows()]

            if layer_count == 2:
                for a in collection_rows:
                    for b in pool_rows:
                        if a["display_name"] == b["display_name"]:
                            continue

                        combo_key = tuple(sorted([a["display_name"], b["display_name"]]))
                        if combo_key in seen:
                            continue
                        seen.add(combo_key)

                        results.append(
                            build_combo_result(
                                [a, b],
                                vibe=st.session_state.vibe,
                                spray_style=st.session_state.spray_style
                            )
                        )

            else:
                for a in collection_rows:
                    for b in pool_rows:
                        for c in pool_rows:
                            names = [a["display_name"], b["display_name"], c["display_name"]]
                            if len(set(names)) < 3:
                                continue

                            combo_key = tuple(sorted(names))
                            if combo_key in seen:
                                continue
                            seen.add(combo_key)

                            results.append(
                                build_combo_result(
                                    [a, b, c],
                                    vibe=st.session_state.vibe,
                                    spray_style=st.session_state.spray_style
                                )
                            )

            st.session_state.latest_combos = sorted(results, key=lambda x: x["score"], reverse=True)[:12]

    if st.session_state.latest_combos:
        st.markdown("#### Your Layering Suggestions")

        for combo in st.session_state.latest_combos:
            combo_key = combo["key"]
            saved_rating = st.session_state.combo_ratings.get(combo_key, "unreviewed")
            rows = combo["rows"]

            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="sniff-name">{combo["combo_name"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sniff-meta">{combo["style"]} layering idea</div>', unsafe_allow_html=True)

            st.write("**Layer these:**")
            for r in rows:
                st.write(f"• {r['display_name']}")

            st.write(f"**Why it works:** {combo['description']}")
            st.write(f"**Spray guide:** {combo['spray_guide']}")
            st.write(f"**Match score:** {combo['score']}")
            st.write(f"**Current rating:** {saved_rating.title() if saved_rating != 'unreviewed' else 'Unreviewed'}")

            r1, r2, r3, r4, r5 = st.columns(5)

            with r1:
                if st.button("Amazing", key=f"amazing_{combo_key}", use_container_width=True):
                    st.session_state.combo_ratings[combo_key] = "amazing"
                    st.rerun()

            with r2:
                if st.button("Good", key=f"good_{combo_key}", use_container_width=True):
                    st.session_state.combo_ratings[combo_key] = "good"
                    st.rerun()

            with r3:
                if st.button("Okay", key=f"neutral_{combo_key}", use_container_width=True):
                    st.session_state.combo_ratings[combo_key] = "neutral"
                    st.rerun()

            with r4:
                if st.button("Bad", key=f"bad_{combo_key}", use_container_width=True):
                    st.session_state.combo_ratings[combo_key] = "bad"
                    st.rerun()

            with r5:
                if st.button("Save", key=f"combo_save_{combo_key}", use_container_width=True):
                    if combo_key not in st.session_state.saved_combo_keys:
                        st.session_state.saved_combo_keys.append(combo_key)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGE: SAVED
# =========================================================
elif st.session_state.page == "Saved":
    st.markdown("### Saved Layering Ideas")

    if st.session_state.saved_combo_keys:
        for item in st.session_state.saved_combo_keys:
            c1, c2 = st.columns([6, 1])
            pretty = item.replace("|||", "  +  ")
            with c1:
                st.markdown(f'<div class="collection-chip"><b>{pretty}</b></div>', unsafe_allow_html=True)
            with c2:
                if st.button("✕", key=f"saved_remove_{item}", use_container_width=True):
                    st.session_state.saved_combo_keys = [
                        x for x in st.session_state.saved_combo_keys if x != item
                    ]
                    st.rerun()
    else:
        st.info("Nothing saved yet.")