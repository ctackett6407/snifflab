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
    df["display"] = df["name"] + " — " + df["brand"]
    return df

df = load_data()

# =========================================================
# UTILS
# =========================================================

def amazon_link(name):
    return f"https://www.amazon.com/s?k={urllib.parse.quote_plus(name)}&tag={AFFILIATE_TAG}"

def get_collection(df):
    return df[df["id"].isin(st.session_state.collection_ids)]

def fragrance_notes(row):
    notes = (
        row.get("top_notes","") + ";" +
        row.get("middle_notes","") + ";" +
        row.get("base_notes","")
    )
    return [n.strip().lower() for n in notes.split(";") if n.strip()]

def fragrance_accords(row):
    accords = [
        row.get("mainaccord1",""),
        row.get("mainaccord2",""),
        row.get("mainaccord3",""),
        row.get("mainaccord4",""),
        row.get("mainaccord5","")
    ]
    return [a.lower() for a in accords if a]

# =========================================================
# COMBO ENGINE
# =========================================================

def combo_score(frags):

    notes = []
    accords = []

    for f in frags:
        notes += fragrance_notes(f)
        accords += fragrance_accords(f)

    score = 0

    shared = len(set(notes))
    score += shared

    synergy = [
        ("vanilla","amber"),
        ("citrus","woody"),
        ("rose","musk"),
        ("coffee","vanilla"),
        ("tobacco","vanilla"),
        ("pear","floral")
    ]

    text = " ".join(notes + accords)

    for a,b in synergy:
        if a in text and b in text:
            score += 3

    clash = [
        ("marine","tobacco"),
        ("aquatic","oud"),
        ("green","dessert")
    ]

    for a,b in clash:
        if a in text and b in text:
            score -= 2

    return score


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
        "Private Blend"
    ]

    return random.choice(styles)


def combo_description(frags):

    names = [f["display"] for f in frags]

    return f"This layering idea blends {', '.join(names)} creating a balanced scent profile where each fragrance adds depth and character."

def spray_guide(style):

    if style == "Conservative":
        return "1 spray chest, 1 neck"

    if style == "Moderate":
        return "2 chest, 1 neck, 1 shirt"

    if style == "Oversprayer":
        return "2 chest, 1 back neck, 1 each side neck, 2 shirt"

    return ""

# =========================================================
# HEADER
# =========================================================

st.title("🧪 SniffLab")
st.caption("Layer your fragrances like a pro.")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    page = st.radio(
        "Menu",
        ["Home","Browse","Collection","Sniff","Saved"]
    )

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

1️⃣ Browse fragrances  
2️⃣ Build your collection  
3️⃣ Generate layering combos  
4️⃣ Save your favorites  
""")

    c1,c2 = st.columns(2)

    with c1:
        if st.button("Browse"):
            st.session_state.page = "Browse"
            st.rerun()

    with c2:
        if st.button("My Collection"):
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
        results = results[results["display"].str.lower().str.contains(search.lower())]

    results = results.head(30)

    for _,row in results.iterrows():

        st.markdown(f"**{row['display']}**")

        c1,c2 = st.columns(2)

        with c1:
            if st.button("Add", key=row["id"]):

                if row["id"] not in st.session_state.collection_ids:
                    st.session_state.collection_ids.append(row["id"])

        with c2:
            st.link_button("Amazon", amazon_link(row["name"]))

        st.divider()

# =========================================================
# COLLECTION
# =========================================================

elif st.session_state.page == "Collection":

    st.subheader("My Collection")

    collection = get_collection(df)

    if collection.empty:
        st.info("Add fragrances from Browse.")
    else:

        for _,row in collection.iterrows():

            c1,c2 = st.columns([6,1])

            with c1:
                st.write(row["display"])

            with c2:
                if st.button("Remove", key=f"rm_{row['id']}"):

                    st.session_state.collection_ids.remove(row["id"])
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

        col1,col2,col3 = st.columns(3)

        with col1:
            st.session_state.layer_count = st.radio(
                "Layers",
                [2,3],
                horizontal=True
            )

        with col2:
            st.session_state.spray_style = st.selectbox(
                "Spray style",
                ["Conservative","Moderate","Oversprayer"]
            )

        with col3:
            st.session_state.vibe = st.selectbox(
                "Vibe",
                ["Any","Sweet","Fresh","Date Night","Clean","Expensive"]
            )

        if st.button("Generate Combos"):

            combos = []

            rows = collection.to_dict("records")

            for a in rows:
                for b in rows:

                    if a["id"] == b["id"]:
                        continue

                    combo = [a,b]

                    if st.session_state.layer_count == 3:
                        for c in rows:
                            if c["id"] in [a["id"],b["id"]]:
                                continue
                            combo = [a,b,c]

                    score = combo_score(combo)

                    combos.append({
                        "frags":combo,
                        "score":score,
                        "name":combo_name(combo),
                        "desc":combo_description(combo)
                    })

            combos = sorted(combos,key=lambda x:x["score"],reverse=True)[:10]

            st.session_state.latest_combos = combos

        for combo in st.session_state.latest_combos:

            st.markdown("### " + combo["name"])

            for f in combo["frags"]:
                st.write("•",f["display"])

            st.write(combo["desc"])

            st.write("Spray:", spray_guide(st.session_state.spray_style))

            key = "|".join([f["id"] for f in combo["frags"]])

            if st.button("Save Combo",key=key):

                if key not in st.session_state.saved_combos:
                    st.session_state.saved_combos.append(key)

            st.divider()

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

            if st.button("Remove",key="del"+combo):

                st.session_state.saved_combos.remove(combo)
                st.rerun()