import streamlit as st
import pandas as pd
import urllib.parse
import random

# =========================================================
# SNIFFLAB V2
# Mobile-first fragrance layering app for TikTok users
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
# SESSION STATE
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
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

theme = THEMES[st.session_state.theme_name]

# =========================================================
# STYLING
# =========================================================
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

        .sniff-meta {{
            color: {theme['muted']};
            font-size: 0.92rem;
            margin-bottom: 0.35rem;
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
    """, unsafe_allow_html=True)

# =========================================================
# DATA HELPERS
# =========================================================
@st.cache_data
def load_fragrances():
    """Load and enrich the fragrance master catalog."""
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

    def pretty_text(value: str) -> str:
        value = str(value).replace("-", " ").replace("_", " ").strip()
        return " ".join(word.capitalize() for word in value.split())

    def split_notes(value: str):
        if not value:
            return []
        return [x.strip() for x in str(value).split(";") if x.strip()]

    def infer_family(row):
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
        axis=1
    )

    df["all_notes"] = df.apply(
        lambda row: list(dict.fromkeys(row["top_list"] + row["middle_list"] + row["base_list"])),
        axis=1
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
    """Fallback affiliate search link."""
    return f"https://www.amazon.com/s?k={urllib.parse.quote_plus(query)}&tag={AFFILIATE_TAG}"


# =========================================================
# COMBO ENGINE
# =========================================================
def combo_score(a, b, vibe, profile, intensity):
    """
    Score a combo based on shared accords, note bridges,
    complementary pairings, vibe/profile match, and intensity.
    """
    accords_a = set(a["accords"])
    accords_b = set(b["accords"])
    notes_a = set([x.lower() for x in a["all_notes"]])
    notes_b = set([x.lower() for x in b["all_notes"]])

    shared_accords = accords_a & accords_b
    shared_notes = notes_a & notes_b

    score = 0
    score += len(shared_accords) * 3
    score += len(shared_notes) * 1.5

    combined = " ".join(list(accords_a | accords_b) + list(notes_a | notes_b))

    # Reliable pairing bonuses
    bonus_pairs = [
        (["vanilla", "amber"], 2.8),
        (["coffee", "vanilla"], 2.3),
        (["cherry", "almond"], 2.5),
        (["tobacco", "vanilla"], 2.8),
        (["floral", "musk"], 1.8),
        (["citrus", "fresh"], 1.8),
        (["woody", "amber"], 2.2),
        (["gourmand", "sweet"], 2.3),
        (["rose", "lychee"], 2.2),
        (["marshmallow", "orange blossom"], 2.2),
        (["bergamot", "woods"], 1.8),
        (["marine", "citrus"], 1.7),
    ]
    for needed, pts in bonus_pairs:
        if all(term in combined for term in needed):
            score += pts

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
            score += 0.9

    for term in profile_terms.get(profile, []):
        if term in combined:
            score += 1.0

    # Intensity shaping
    if intensity == "Easy":
        if len(shared_accords) >= 2:
            score += 1.2
    elif intensity == "Signature":
        if len(shared_accords) >= 1 and len(shared_notes) >= 1:
            score += 1.5
    elif intensity == "Beast Mode":
        if any(x in combined for x in ["amber", "vanilla", "tobacco", "oud", "coffee", "boozy"]):
            score += 2.0
    elif intensity == "Experimental":
        if len(shared_accords) >= 1:
            score += 0.5

    return round(score, 2)


def combo_tier(score: float, intensity: str) -> str:
    """Assign a fun combo tier."""
    if intensity == "Beast Mode":
        if score >= 10:
            return "Beast Mode"
        return "Signature Blend"

    if intensity == "Experimental":
        if score >= 9:
            return "Wild Card"
        return "Experimental"

    if score >= 10:
        return "Signature Blend"
    if score >= 8:
        return "Easy Win"
    if score >= 6.5:
        return "Date Night"
    return "Clean Flex"


def combo_name(a, b, tier):
    """Generate fun combo names."""
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


def combo_description(a, b, vibe, profile):
    """Human-readable explanation."""
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
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    st.header("SniffLab")

    page = st.radio(
        "Go to",
        ["Home", "Browse", "Collection", "Saved", "Settings"],
        index=["Home", "Browse", "Collection", "Saved", "Settings"].index(st.session_state.page)
    )
    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()

    st.divider()
    st.caption("As an Amazon Associate I earn from qualifying purchases.")

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="main-title">🧪 SniffLab</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Fragrance layering made simple.</div>', unsafe_allow_html=True)
st.markdown('<div class="hint-box">On mobile, tap <b>››</b> in the top-left corner to open the menu.</div>', unsafe_allow_html=True)

if st.session_state.last_added:
    st.toast(f"Added: {st.session_state.last_added}")
    st.session_state.last_added = ""

# =========================================================
# PAGE: HOME (SNIFF FIRST)
# =========================================================
if st.session_state.page == "Home":
    st.markdown("### Sniff")

    st.markdown(f"""
    <div class="hero-box">
    <b>Your Collection</b><br>
    {len(st.session_state.my_collection)} fragrance(s) ready to layer
    </div>
    """, unsafe_allow_html=True)

    source_mode = st.segmented_control(
        "Source",
        ["My Collection", "Collection + Community"],
        selection_mode="single",
        default=st.session_state.source_mode
    )
    st.session_state.source_mode = source_mode

    c1, c2, c3 = st.columns(3)

    with c1:
        vibe = st.selectbox(
            "Vibe",
            ["Any", "Sexy", "Clean", "Cozy", "Night Out", "Soft"],
            index=["Any", "Sexy", "Clean", "Cozy", "Night Out", "Soft"].index(st.session_state.vibe)
        )
        st.session_state.vibe = vibe

    with c2:
        profile = st.selectbox(
            "Scent Profile",
            ["Any", "Gourmand", "Floral", "Fresh", "Woody", "Fruity"],
            index=["Any", "Gourmand", "Floral", "Fresh", "Woody", "Fruity"].index(st.session_state.profile)
        )
        st.session_state.profile = profile

    with c3:
        intensity = st.selectbox(
            "Intensity",
            ["Easy", "Signature", "Beast Mode", "Experimental"],
            index=["Easy", "Signature", "Beast Mode", "Experimental"].index(st.session_state.intensity)
        )
        st.session_state.intensity = intensity

    st.caption("Set the mood, then tap 🧪 Sniff to generate layering ideas.")

    if st.button("🧪 Sniff", type="primary"):
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

                    score = combo_score(a, b, vibe, profile, intensity)
                    tier = combo_tier(score, intensity)

                    results.append({
                        "a": a,
                        "b": b,
                        "score": score,
                        "tier": tier,
                        "combo_name": combo_name(a, b, tier),
                        "description": combo_description(a, b, vibe, profile),
                        "key": f"{key[0]}|||{key[1]}"
                    })

            st.session_state.latest_combos = sorted(results, key=lambda x: x["score"], reverse=True)[:12]

    if st.session_state.latest_combos:
        st.markdown("### Your Combos")

        for combo in st.session_state.latest_combos:
            a = combo["a"]
            b = combo["b"]
            combo_key = combo["key"]
            saved_rating = st.session_state.combo_ratings.get(combo_key, "unreviewed")

            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="tier-chip">{combo["tier"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sniff-name">{combo["combo_name"]}</div>', unsafe_allow_html=True)
            st.write(f"**Layer:** {a['display_name']} + {b['display_name']}")
            st.write(f"**Why it works:** {combo['description']}")
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

            r6.link_button("🛒", amazon_search_link(b["name_pretty"]))
            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# PAGE: BROWSE
# =========================================================
elif st.session_state.page == "Browse":
    st.markdown("### Browse Fragrances")

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
            index=options.index(st.session_state.brand_filter) if st.session_state.brand_filter in options else 0
        )
        st.session_state.brand_filter = brand_filter

    with f2:
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

    filtered_df = filtered_df[~filtered_df["display_name"].isin(st.session_state.my_collection)].copy()
    filtered_df["brand_priority"] = filtered_df["brand"].str.lower().apply(lambda x: 0 if x == "desmirage" else 1)
    filtered_df = filtered_df.sort_values(["brand_priority", "brand_pretty", "name_pretty"], ascending=[True, True, True])

    results_df = filtered_df.head(30)

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
            accord_text = ", ".join(accords) if accords else "—"

            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)

            st.markdown(
                f'<div class="sniff-name">{family_icon(row["family"])} {row["name_pretty"]}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="sniff-meta"><b>{row["brand_pretty"]}</b></div>',
                unsafe_allow_html=True
            )

            if row["inspired_by"]:
                st.markdown(
                    f'<div class="mini-label">Inspired by</div><div>{row["inspired_by"]}</div>',
                    unsafe_allow_html=True
                )

            st.markdown(
                f'<div class="mini-label">Family</div><div>{row["family"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="mini-label">Top Notes</div><div>{top_notes}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="mini-label">Middle Notes</div><div>{middle_notes}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="mini-label">Base Notes</div><div>{base_notes}</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="mini-label">Accords</div><div>{accord_text}</div>',
                unsafe_allow_html=True
            )

            b1, b2, b3 = st.columns(3)

            if b1.button("➕", key=f"add_{row['id']}"):
                if row["display_name"] not in st.session_state.my_collection:
                    st.session_state.my_collection.append(row["display_name"])
                st.session_state.last_added = row["display_name"]
                st.rerun()

            if b2.button("⭐", key=f"save_frag_{row['id']}"):
                if row["display_name"] not in st.session_state.sniff_list:
                    st.session_state.sniff_list.append(row["display_name"])
                st.rerun()

            b3.link_button("🛒", amazon_search_link(f"{row['brand_pretty']} {row['name_pretty']}"))

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
                    st.session_state.my_collection = [x for x in st.session_state.my_collection if x != row["display_name"]]
                    st.rerun()
    else:
        st.info("Your collection is empty.")

# =========================================================
# PAGE: SAVED
# =========================================================
elif st.session_state.page == "Saved":
    st.markdown("### Saved")

    st.markdown("#### ⭐ Sniff List")
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
# PAGE: SETTINGS
# =========================================================
elif st.session_state.page == "Settings":
    st.markdown("### Settings")

    selected_theme = st.selectbox(
        "Theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme_name)
    )
    if selected_theme != st.session_state.theme_name:
        st.session_state.theme_name = selected_theme
        st.rerun()

    st.markdown("""
    <div class="hero-box">
    <b>Icons</b><br><br>
    ➕ Add<br>
    ⭐ Save<br>
    ✕ Remove<br>
    🛒 Check Price<br>
    🧪 Sniff
    </div>
    """, unsafe_allow_html=True)