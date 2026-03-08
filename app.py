import streamlit as st
import pandas as pd
import urllib.parse

# =========================================================
# SNIFFLAB CONFIG
# =========================================================
# Main catalog file the app reads from
CSV_PATH = "data/fragrances_master.csv"

# Amazon affiliate tag for product search links
AFFILIATE_TAG = "christacket04-20"

# Basic Streamlit page config
st.set_page_config(
    page_title="SniffLab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# THEME PRESETS
# =========================================================
# "System Default" means no custom CSS theme is applied.
# The others apply a full preset color style across cards,
# buttons, chips, text, and inputs.
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
        # More exaggerated, vibrant pink theme
        "bg": "#FFF0F8",
        "card": "#FFDCF1",
        "text": "#4A1030",
        "muted": "#A63A72",
        "accent": "#FF2DAA",
        "border": "#FF8DCA",
        "button_bg": "#FF1493",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#C40078",
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
        # Candy-like, explosive rainbow feel
        "bg": "#FFF7FB",
        "card": "#FFFFFF",
        "text": "#24123A",
        "muted": "#7D5AA6",
        "accent": "#FF4FD8",
        "border": "#7C3AED",
        "button_bg": "#FF5E5B",
        "button_text": "#FFFFFF",
        "button_hover_bg": "#00C2FF",
        "button_hover_text": "#111111",
    },
}

# =========================================================
# SESSION STATE DEFAULTS
# =========================================================
# These keep the app stateful during a session so the user
# can browse, add, sniff, and save without losing progress.
if "theme_name" not in st.session_state:
    st.session_state.theme_name = "System Default"

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "my_collection" not in st.session_state:
    st.session_state.my_collection = []

if "sniff_list" not in st.session_state:
    st.session_state.sniff_list = []

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

# Current active theme preset
theme = THEMES[st.session_state.theme_name]

# =========================================================
# GLOBAL APP STYLING
# =========================================================
# If the user selects "System Default", this CSS block is skipped
# so the app uses normal Streamlit styling.
if theme is not None:
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {theme['bg']};
            color: {theme['text']};
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
            margin-bottom: 10px;
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
        }}

        .hero-box {{
            background: {theme['card']};
            border: 1px solid {theme['border']};
            border-radius: 20px;
            padding: 16px;
            margin-bottom: 14px;
        }}

        .small-note {{
            color: {theme['muted']};
            font-size: 0.86rem;
        }}

        /* =========================
           BUTTONS
           ========================= */
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

        /* =========================
           INPUTS / SELECTS
           ========================= */
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

        /* =========================
           LINK BUTTONS
           ========================= */
        .stLinkButton a {{
            background-color: {theme['card']} !important;
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
            background-color: {theme['accent']} !important;
            color: {theme['button_hover_text']} !important;
            border-color: {theme['accent']} !important;
            -webkit-text-fill-color: {theme['button_hover_text']} !important;
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

    def infer_family(row):
        """
        Lightweight family detection for grouping collection items.
        """
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

    df["top_list"] = df["top_notes"].apply(split_notes)
    df["middle_list"] = df["middle_notes"].apply(split_notes)
    df["base_list"] = df["base_notes"].apply(split_notes)

    df["accords"] = df[
        ["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]
    ].apply(
        lambda row: [x.strip().lower() for x in row.tolist() if str(x).strip()],
        axis=1
    )

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


def combo_score(a, b, mood):
    """
    Very lightweight pairing score based on shared accords,
    shared notes, and a few simple bonus rules.
    """
    accords_a = set(a["accords"])
    accords_b = set(b["accords"])
    notes_a = set([x.lower() for x in a["all_notes"]])
    notes_b = set([x.lower() for x in b["all_notes"]])

    shared_accords = accords_a & accords_b
    shared_notes = notes_a & notes_b
    score = len(shared_accords) * 3 + len(shared_notes) * 1.5

    combined_text = " ".join(list(accords_a | accords_b) + list(notes_a | notes_b))

    bonus_pairs = [
        (["vanilla", "amber"], 2.5),
        (["coffee", "vanilla"], 2.0),
        (["cherry", "almond"], 2.0),
        (["tobacco", "vanilla"], 2.5),
        (["floral", "musk"], 1.8),
        (["citrus", "fresh"], 1.8),
        (["woody", "amber"], 2.0),
        (["gourmand", "sweet"], 2.2),
    ]
    for needed, pts in bonus_pairs:
        if all(n in combined_text for n in needed):
            score += pts

    mood_terms = {
        "Any": [],
        "Gourmand": ["gourmand", "sweet", "vanilla", "dessert", "marzipan", "caramel"],
        "Floral": ["floral", "rose", "jasmine", "orange blossom", "neroli", "iris"],
        "Fresh": ["fresh", "citrus", "marine", "bergamot", "lemon", "mint"],
        "Woody / Warm": ["woody", "amber", "cedar", "sandalwood", "tobacco", "patchouli"],
        "Fruity": ["fruity", "pear", "mango", "cherry", "peach", "plum", "lychee"],
    }
    for term in mood_terms.get(mood, []):
        if term in combined_text:
            score += 0.8

    return round(score, 2)


def combo_description(a, b):
    """Short plain-English combo summary."""
    text = " ".join(a["accords"] + b["accords"] + [x.lower() for x in a["all_notes"] + b["all_notes"]])

    if any(x in text for x in ["gourmand", "vanilla", "sweet", "dessert"]):
        return "Sweet, creamy layering with a cozy dessert-like feel."
    if any(x in text for x in ["floral", "rose", "jasmine", "orange blossom"]):
        return "Soft floral layering with lift and smooth sweetness."
    if any(x in text for x in ["fresh", "citrus", "marine", "bergamot"]):
        return "Bright, airy layering that feels clean and easy to wear."
    if any(x in text for x in ["woody", "amber", "tobacco", "patchouli"]):
        return "Rich, warm layering with depth and an expensive feel."
    if any(x in text for x in ["fruity", "pear", "mango", "cherry"]):
        return "Juicy, playful layering with added brightness and dimension."
    return "Balanced layering with shared notes and complementary structure."


def combo_name(a, b):
    """Simple combo naming logic."""
    one = a["name_pretty"].split()[0]
    two = b["name_pretty"].split()[0]
    if one.lower() != two.lower():
        return f"{one} x {two}"
    return f"{a['name_pretty']} Blend"

# Load catalog once
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

    # Theme selector, including "System Default"
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
    4. Use <b>⭐</b> to save things for later.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    if c1.button("Browse Fragrances"):
        st.session_state.page = "Browse"
        st.rerun()
    if c2.button("Open My Collection"):
        st.session_state.page = "Collection"
        st.rerun()

    st.caption("➕ Add  •  ⭐ Save  •  ✕ Remove  •  🛒 Check Price")

# =========================================================
# PAGE: BROWSE
# =========================================================
elif st.session_state.page == "Browse":
    st.markdown("### Browse Fragrances")

    # Quick brand buttons
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

    # Search / filter controls
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

    # Apply filters
    filtered_df = df.copy()

    if brand_filter != "All Brands":
        filtered_df = filtered_df[filtered_df["brand_pretty"] == brand_filter]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[filtered_df["search_text"].str.contains(q, na=False)]

    # Hide items already in the user's collection
    filtered_df = filtered_df[~filtered_df["display_name"].isin(st.session_state.my_collection)].copy()

    # Prioritize desmirage slightly in browse results
    filtered_df["brand_priority"] = filtered_df["brand"].str.lower().apply(lambda x: 0 if x == "desmirage" else 1)
    filtered_df = filtered_df.sort_values(["brand_priority", "brand_pretty", "name_pretty"], ascending=[True, True, True])

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

            accord_text = ", ".join([
                x for x in [
                    row["mainaccord1"],
                    row["mainaccord2"],
                    row["mainaccord3"],
                    row["mainaccord4"],
                    row["mainaccord5"]
                ] if x
            ])
            if accord_text:
                st.markdown(f'<div class="mini-label">Accords</div><div>{accord_text}</div>', unsafe_allow_html=True)

            b1, b2 = st.columns(2)

            if b1.button("➕", key=f"add_{row['id']}"):
                if row["display_name"] not in st.session_state.my_collection:
                    st.session_state.my_collection.append(row["display_name"])
                st.session_state.last_added = row["display_name"]
                st.rerun()

            if b2.button("⭐", key=f"save_{row['id']}"):
                if row["display_name"] not in st.session_state.sniff_list:
                    st.session_state.sniff_list.append(row["display_name"])
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGE: COLLECTION
# =========================================================
elif st.session_state.page == "Collection":
    st.markdown("### My Collection")

    if st.session_state.my_collection:
        collection_df = df[df["display_name"].isin(st.session_state.my_collection)].copy()

        for family in ["Gourmand", "Floral", "Fresh", "Woody / Warm", "Fruity", "Other"]:
            family_rows = collection_df[collection_df["family"] == family]
            if family_rows.empty:
                continue

            st.markdown(f"#### {family_icon(family)} {family}")
            for _, row in family_rows.sort_values("display_name").iterrows():
                c1, c2 = st.columns([6, 1])
                c1.markdown(f'<div class="collection-chip"><b>{row["display_name"]}</b></div>', unsafe_allow_html=True)
                if c2.button("✕", key=f"remove_{row['display_name']}"):
                    st.session_state.my_collection = [
                        x for x in st.session_state.my_collection if x != row["display_name"]
                    ]
                    st.rerun()
    else:
        st.info("Your collection is empty.")

# =========================================================
# PAGE: SNIFF
# =========================================================
elif st.session_state.page == "Sniff":
    st.markdown("### Sniff")

    sniff_col1, sniff_col2 = st.columns(2)

    with sniff_col1:
        sniff_mode = st.radio(
            "Use",
            ["My Collection Only", "My Collection + Community Fragrances"],
            index=["My Collection Only", "My Collection + Community Fragrances"].index(st.session_state.sniff_mode)
        )
        st.session_state.sniff_mode = sniff_mode

    with sniff_col2:
        mood = st.selectbox(
            "Mood",
            ["Any", "Gourmand", "Floral", "Fresh", "Woody / Warm", "Fruity"],
            index=["Any", "Gourmand", "Floral", "Fresh", "Woody / Warm", "Fruity"].index(st.session_state.mood)
        )
        st.session_state.mood = mood

    st.caption("Tap 🧪 to generate layering ideas from what you own.")

    if st.button("🧪 Sniff", type="primary"):
        collection_df = df[df["display_name"].isin(st.session_state.my_collection)].copy()

        if collection_df.empty:
            st.warning("Add at least one fragrance to My Collection first.")
        else:
            pool_df = collection_df.copy() if sniff_mode == "My Collection Only" else df.copy()
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

                    results.append({
                        "a": a,
                        "b": b,
                        "score": combo_score(a, b, mood),
                        "combo_name": combo_name(a, b),
                        "description": combo_description(a, b),
                        "key": f"{key[0]}|||{key[1]}"
                    })

            st.session_state.latest_combos = sorted(results, key=lambda x: x["score"], reverse=True)[:12]

    if st.session_state.latest_combos:
        st.markdown("#### Your Layering Suggestions")

        for combo in st.session_state.latest_combos:
            a = combo["a"]
            b = combo["b"]
            combo_key = combo["key"]
            saved_rating = st.session_state.combo_ratings.get(combo_key, "unreviewed")

            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="sniff-name">{combo["combo_name"]}</div>', unsafe_allow_html=True)
            st.write(f"**Layer:** {a['display_name']} + {b['display_name']}")
            st.write(f"**Why it may work:** {combo['description']}")
            st.write(f"**Mood fit score:** {combo['score']}")
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
            if r5.button("⭐", key=f"combo_save_{combo_key}"):
                if b["display_name"] not in st.session_state.sniff_list:
                    st.session_state.sniff_list.append(b["display_name"])
                st.rerun()

            r6.link_button("🛒", amazon_search_link(b["name_pretty"]))
            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGE: SAVED
# =========================================================
elif st.session_state.page == "Saved":
    st.markdown("### Sniff List")

    if st.session_state.sniff_list:
        for item in st.session_state.sniff_list:
            c1, c2 = st.columns([6, 1])
            c1.markdown(f'<div class="collection-chip"><b>{item}</b></div>', unsafe_allow_html=True)
            if c2.button("✕", key=f"saved_remove_{item}"):
                st.session_state.sniff_list = [x for x in st.session_state.sniff_list if x != item]
                st.rerun()
    else:
        st.info("Nothing saved yet.")