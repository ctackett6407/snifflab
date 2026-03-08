import streamlit as st
import pandas as pd
import random
import urllib.parse

# =========================================================
# CONFIG
# =========================================================

CSV_PATH = "data/fragrances_master.csv"
AFFILIATE_TAG = "christacket04-20"

st.set_page_config(
    page_title="SniffLab",
    page_icon="🧪",
    layout="wide",
)

# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "collection_ids" not in st.session_state:
    st.session_state.collection_ids = []

if "saved_combos" not in st.session_state:
    st.session_state.saved_combos = []

if "latest_combos" not in st.session_state:
    st.session_state.latest_combos = []

if "spray_style" not in st.session_state:
    st.session_state.spray_style = "Moderate"

if "layer_count" not in st.session_state:
    st.session_state.layer_count = 2

if "vibe" not in st.session_state:
    st.session_state.vibe = "Any"

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

    # Build a display field
    if "name" not in df.columns:
        df["name"] = ""
    if "brand" not in df.columns:
        df["brand"] = ""
    if "id" not in df.columns:
        df["id"] = (
            df["brand"].astype(str).str.lower().str.strip() + "||" +
            df["name"].astype(str).str.lower().str.strip()
        )

    df["display"] = df["name"].astype(str) + " — " + df["brand"].astype(str)
    return df

df = load_data()

# =========================================================
# UTILS
# =========================================================

def amazon_link(name):
    return f"https://www.amazon.com/s?k={urllib.parse.quote_plus(name)}&tag={AFFILIATE_TAG}"

def get_collection(df_):
    return df_[df_["id"].isin(st.session_state.collection_ids)].copy()

def fragrance_notes(row):
    notes = (
        str(row.get("top_notes", "")) + ";" +
        str(row.get("middle_notes", "")) + ";" +
        str(row.get("base_notes", ""))
    )
    return [n.strip().lower() for n in notes.split(";") if n.strip()]

def fragrance_accords(row):
    accords = [
        str(row.get("mainaccord1", "")),
        str(row.get("mainaccord2", "")),
        str(row.get("mainaccord3", "")),
        str(row.get("mainaccord4", "")),
        str(row.get("mainaccord5", "")),
    ]
    return [a.strip().lower() for a in accords if a.strip()]

# =========================================================
# COMBO ENGINE
# =========================================================

def combo_score(frags):
    notes = []
    accords = []

    for frag in frags:
        notes += fragrance_notes(frag)
        accords += fragrance_accords(frag)

    score = 0

    unique_notes = len(set(notes))
    unique_accords = len(set(accords))
    score += unique_notes * 0.6
    score += unique_accords * 1.2

    synergy = [
        ("vanilla", "amber"),
        ("citrus", "woody"),
        ("rose", "musk"),
        ("coffee", "vanilla"),
        ("tobacco", "vanilla"),
        ("pear", "floral"),
        ("fresh", "musk"),
        ("cherry", "vanilla"),
    ]

    text = " ".join(notes + accords)

    for a, b in synergy:
        if a in text and b in text:
            score += 3

    clash = [
        ("marine", "tobacco"),
        ("aquatic", "oud"),
        ("green", "dessert"),
        ("powdery", "marine"),
    ]

    for a, b in clash:
        if a in text and b in text:
            score -= 2

    if st.session_state.vibe == "Sweet":
        for word in ["vanilla", "sweet", "gourmand", "caramel", "praline"]:
            if word in text:
                score += 1
    elif st.session_state.vibe == "Fresh":
        for word in ["fresh", "citrus", "marine", "bergamot", "mint"]:
            if word in text:
                score += 1
    elif st.session_state.vibe == "Date Night":
        for word in ["amber", "musk", "vanilla", "rose", "tobacco"]:
            if word in text:
                score += 1
    elif st.session_state.vibe == "Clean":
        for word in ["fresh", "soap", "musk", "white floral"]:
            if word in text:
                score += 1
    elif st.session_state.vibe == "Expensive":
        for word in ["iris", "amber", "woody", "sandalwood", "musk"]:
            if word in text:
                score += 1

    return round(score, 2)

def combo_name(frags):
    styles = [
        "Velvet Static",
        "Sugar Signal",
        "Clean Voltage",
        "Midnight Layer",
        "Soft Chemistry",
        "Amber Pulse",
        "Golden Drift",
        "After Hours",
        "Neon Fruit",
        "Private Blend",
        "Skin Echo",
        "Citrus Halo",
    ]
    return random.choice(styles)

def combo_description(frags):
    names = [f["display"] for f in frags]
    if len(names) == 2:
        joined = f"{names[0]} and {names[1]}"
    else:
        joined = f"{names[0]}, {names[1]}, and {names[2]}"
    return f"This layering idea blends {joined}, creating a more rounded scent profile with extra depth and character."

def spray_guide(style, frags):
    text = " ".join(
        [note for frag in frags for note in fragrance_notes(frag)] +
        [acc for frag in frags for acc in fragrance_accords(frag)]
    )

    dense = any(x in text for x in ["oud", "tobacco", "amber", "patchouli", "sweet", "gourmand"])
    fresh = any(x in text for x in ["fresh", "citrus", "marine", "mint", "aquatic"])

    if style == "Conservative":
        if dense:
            return "1 spray on chest, 1 on lower neck."
        if fresh:
            return "1 on chest, 1 on neck, optional 1 on shirt."
        return "1 on chest, 1 on neck."

    if style == "Oversprayer":
        if dense:
            return "2 on chest, 1 back of neck, 1 shirt."
        if fresh:
            return "2 on chest, 1 back of neck, 1 each side of neck, 2 on shirt."
        return "2 on chest, 1 back of neck, 1 each side of neck, 1 shirt."

    if dense:
        return "2 on chest, 1 lower neck, optional 1 back of neck."
    if fresh:
        return "2 on chest, 1 neck, 1 shirt."
    return "2 on chest, 1 neck, 1 shirt."

# =========================================================
# SIMPLE STYLING
# =========================================================

st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 4rem;
}
.sniff-card {
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.title("🧪 SniffLab")
st.caption("Layer your fragrances like a pro.")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    page = st.radio("Menu", ["Home", "Browse", "Collection", "Sniff", "Saved"])
    st.session_state.page = page
    st.divider()
    st.caption("Amazon affiliate links may be used.")

# =========================================================
# HOME
# =========================================================

if st.session_state.page == "Home":
    st.subheader("Welcome")
    st.markdown("""
SniffLab helps you:

1. Browse fragrances  
2. Build your collection  
3. Generate layering combos  
4. Save your favorites
""")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Browse", use_container_width=True):
            st.session_state.page = "Browse"
            st.rerun()
    with c2:
        if st.button("My Collection", use_container_width=True):
            st.session_state.page = "Collection"
            st.rerun()

# =========================================================
# BROWSE
# =========================================================

elif st.session_state.page == "Browse":
    st.subheader("Browse Fragrances")

    search = st.text_input("Search")
    results = df.copy()

    if search:
        results = results[results["display"].str.lower().str.contains(search.lower(), na=False)]

    results = results[~results["id"].isin(st.session_state.collection_ids)].copy()
    results = results.head(30)

    st.caption(f"{len(results)} fragrances available")

    for _, row in results.iterrows():
        st.markdown('<div class="sniff-card">', unsafe_allow_html=True)
        st.markdown(f"**{row['display']}**")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Add", key=f"add_{row['id']}", use_container_width=True):
                if row["id"] not in st.session_state.collection_ids:
                    st.session_state.collection_ids.append(row["id"])
                st.rerun()

        with c2:
            st.link_button("Amazon", amazon_link(row["name"]), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# COLLECTION
# =========================================================

elif st.session_state.page == "Collection":
    st.subheader("My Collection")

    collection = get_collection(df)

    if collection.empty:
        st.info("Add fragrances from Browse.")
    else:
        for _, row in collection.iterrows():
            c1, c2 = st.columns([6, 1])
            with c1:
                st.write(row["display"])
            with c2:
                if st.button("Remove", key=f"rm_{row['id']}", use_container_width=True):
                    st.session_state.collection_ids = [
                        x for x in st.session_state.collection_ids if x != row["id"]
                    ]
                    st.rerun()

# =========================================================
# SNIFF
# =========================================================

elif st.session_state.page == "Sniff":
    st.subheader("Layering Lab")

    collection = get_collection(df)

    if collection.empty:
        st.warning("Add fragrances first.")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.session_state.layer_count = st.radio(
                "Layers",
                [2, 3],
                index=[2, 3].index(st.session_state.layer_count),
                horizontal=True
            )

        with col2:
            st.session_state.spray_style = st.selectbox(
                "Spray style",
                ["Conservative", "Moderate", "Oversprayer"],
                index=["Conservative", "Moderate", "Oversprayer"].index(st.session_state.spray_style)
            )

        with col3:
            st.session_state.vibe = st.selectbox(
                "Vibe",
                ["Any", "Sweet", "Fresh", "Date Night", "Clean", "Expensive"],
                index=["Any", "Sweet", "Fresh", "Date Night", "Clean", "Expensive"].index(st.session_state.vibe)
            )

        if st.button("Generate Combos", type="primary", use_container_width=True):
            combos = []
            seen = set()
            rows = collection.to_dict("records")

            if st.session_state.layer_count == 2:
                for i in range(len(rows)):
                    for j in range(i + 1, len(rows)):
                        combo = [rows[i], rows[j]]
                        key = tuple(sorted([rows[i]["id"], rows[j]["id"]]))
                        if key in seen:
                            continue
                        seen.add(key)

                        combos.append({
                            "frags": combo,
                            "score": combo_score(combo),
                            "name": combo_name(combo),
                            "desc": combo_description(combo),
                        })
            else:
                for i in range(len(rows)):
                    for j in range(i + 1, len(rows)):
                        for k in range(j + 1, len(rows)):
                            combo = [rows[i], rows[j], rows[k]]
                            key = tuple(sorted([rows[i]["id"], rows[j]["id"], rows[k]["id"]]))
                            if key in seen:
                                continue
                            seen.add(key)

                            combos.append({
                                "frags": combo,
                                "score": combo_score(combo),
                                "name": combo_name(combo),
                                "desc": combo_description(combo),
                            })

            combos = sorted(combos, key=lambda x: x["score"], reverse=True)[:10]
            st.session_state.latest_combos = combos

        for combo in st.session_state.latest_combos:
            st.markdown('<div class="sniff-card">', unsafe_allow_html=True)
            st.markdown(f"### {combo['name']}")

            for frag in combo["frags"]:
                st.write("•", frag["display"])

            st.write(combo["desc"])
            st.write("**Score:**", combo["score"])
            st.write("**Spray:**", spray_guide(st.session_state.spray_style, combo["frags"]))

            key = "|".join(sorted([f["id"] for f in combo["frags"]]))
            if st.button("Save Combo", key=f"save_{key}", use_container_width=True):
                if key not in st.session_state.saved_combos:
                    st.session_state.saved_combos.append(key)

            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# SAVED
# =========================================================

elif st.session_state.page == "Saved":
    st.subheader("Saved Combos")

    if not st.session_state.saved_combos:
        st.info("No saved combos yet.")
    else:
        for combo in st.session_state.saved_combos:
            st.write(combo)
            if st.button("Remove", key=f"del_{combo}", use_container_width=True):
                st.session_state.saved_combos.remove(combo)
                st.rerun()