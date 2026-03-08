import streamlit as st
import pandas as pd
import random
import urllib.parse

st.set_page_config(page_title="SniffLab", page_icon="🧪", layout="wide")

CSV_PATH = "data/fragrances.csv"
AFFILIATE_TAG = "christacket04-20"


@st.cache_data
def load_fragrances():
    df = pd.read_csv(CSV_PATH, sep=";", encoding="latin1")

    # Clean expected columns
    expected_cols = [
        "url", "Perfume", "Brand", "Country", "Gender", "Rating Value",
        "Rating Count", "Year", "Top", "Middle", "Base",
        "Perfumer1", "Perfumer2",
        "mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Keep only real perfume rows
    df = df[df["Perfume"] != ""].copy()

    # Normalize rating columns
    df["rating_count_num"] = pd.to_numeric(df["Rating Count"], errors="coerce").fillna(0)
    df["rating_value_num"] = pd.to_numeric(df["Rating Value"], errors="coerce").fillna(0)

    # Normalize display text
    def pretty_text(value: str) -> str:
        value = value.replace("-", " ").replace("_", " ").strip()
        return " ".join(word.capitalize() for word in value.split())

    df["perfume_pretty"] = df["Perfume"].apply(pretty_text)
    df["brand_pretty"] = df["Brand"].apply(pretty_text)
    df["display_name"] = df["perfume_pretty"] + " — " + df["brand_pretty"]

    # Search text includes perfume + brand + accords + notes
    note_cols = ["Top", "Middle", "Base", "mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]
    df["search_text"] = (
        df["Perfume"].str.lower() + " " +
        df["Brand"].str.lower() + " " +
        df[note_cols].agg(" ".join, axis=1).str.lower()
    )

    # Collect accords
    accord_cols = ["mainaccord1", "mainaccord2", "mainaccord3", "mainaccord4", "mainaccord5"]
    df["accords"] = df[accord_cols].apply(
        lambda row: [x.strip().lower() for x in row.tolist() if x.strip()],
        axis=1
    )

    # Collect notes
    def split_notes(raw: str):
        if not raw:
            return []
        parts = [p.strip().lower() for p in raw.replace("\t", ";").split(";")]
        return [p for p in parts if p]

    df["top_notes"] = df["Top"].apply(split_notes)
    df["middle_notes"] = df["Middle"].apply(split_notes)
    df["base_notes"] = df["Base"].apply(split_notes)
    df["all_notes"] = df.apply(
        lambda row: list(dict.fromkeys(row["top_notes"] + row["middle_notes"] + row["base_notes"])),
        axis=1
    )

    # Simple family label
    def infer_family(row):
        accords = set(row["accords"])
        notes = set(row["all_notes"])

        if {"gourmand", "sweet", "vanilla", "dessert", "milky", "marzipan"} & accords:
            return "Gourmand"
        if {"floral", "white floral", "rose"} & accords:
            return "Floral"
        if {"marine", "fresh", "citrus", "aromatic"} & accords:
            return "Fresh"
        if {"woody", "amber", "warm spicy", "tobacco"} & accords:
            return "Woody / Warm"
        if {"fruity", "cherry", "tropical"} & accords:
            return "Fruity"
        if {"vanilla", "caramel", "marshmallow"} & notes:
            return "Gourmand"
        return "Other"

    df["family"] = df.apply(infer_family, axis=1)

    return df


def amazon_search_link(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.amazon.com/s?k={encoded}&tag={AFFILIATE_TAG}"


def combo_score(a: pd.Series, b: pd.Series, mood: str) -> float:
    accords_a = set(a["accords"])
    accords_b = set(b["accords"])
    notes_a = set(a["all_notes"])
    notes_b = set(b["all_notes"])

    shared_accords = accords_a & accords_b
    shared_notes = notes_a & notes_b

    score = 0.0
    score += len(shared_accords) * 3
    score += len(shared_notes) * 1.5

    # Helpful complementary boosts
    pair_text = " ".join(list(accords_a | accords_b) + list(notes_a | notes_b))

    boosts = [
        (["vanilla", "amber"], 2.5),
        (["marshmallow", "caramel"], 2.0),
        (["citrus", "fresh"], 2.0),
        (["woody", "amber"], 2.0),
        (["floral", "musk"], 1.5),
        (["coffee", "vanilla"], 2.0),
        (["cherry", "almond"], 2.0),
        (["tobacco", "vanilla"], 2.5),
        (["marine", "citrus"], 1.5),
        (["fruity", "musk"], 1.5),
    ]
    for needed, pts in boosts:
        if all(term in pair_text for term in needed):
            score += pts

    # Mood steering
    mood_map = {
        "Any": [],
        "Gourmand": ["gourmand", "sweet", "vanilla", "dessert", "milky", "marzipan", "caramel"],
        "Floral": ["floral", "white floral", "rose", "jasmine", "orange blossom", "neroli"],
        "Fresh": ["fresh", "citrus", "marine", "aromatic", "bergamot", "lemon", "grapefruit"],
        "Woody / Warm": ["woody", "amber", "warm spicy", "tobacco", "cedar", "sandalwood"],
        "Fruity": ["fruity", "tropical", "cherry", "pear", "mango", "black currant"],
    }

    if mood in mood_map:
        score += sum(1 for term in mood_map[mood] if term in pair_text) * 0.8

    # Tiny bonus for desmirage so it surfaces nicely
    if a["Brand"].lower() == "desmirage" or b["Brand"].lower() == "desmirage":
        score += 0.25

    return round(score, 2)


def combo_description(a: pd.Series, b: pd.Series) -> str:
    key = set(a["accords"] + b["accords"] + a["all_notes"] + b["all_notes"])

    if {"gourmand", "vanilla", "sweet"} & key:
        return "Sweet, creamy, dessert-like layering with a cozy finish."
    if {"floral", "white floral", "rose", "jasmine"} & key:
        return "Soft floral layering with lift, glow, and smooth sweetness."
    if {"citrus", "fresh", "marine", "aromatic"} & key:
        return "Bright, clean, fresh layering that feels airy and easy to wear."
    if {"woody", "amber", "warm spicy", "tobacco"} & key:
        return "Rich, warm layering with depth and an expensive feel."
    if {"fruity", "cherry", "pear", "mango"} & key:
        return "Juicy, playful fruit-forward layering with added dimension."
    return "Balanced layering with shared notes and complementary structure."


def combo_name(a: pd.Series, b: pd.Series) -> str:
    words = []
    for candidate in [a["perfume_pretty"], b["perfume_pretty"]]:
        first = candidate.split()[0]
        if first not in words:
            words.append(first)

    if len(words) >= 2:
        return f"{words[0]} x {words[1]}"
    return f"{a['perfume_pretty']} Blend"


def rating_to_label(rating_value: str) -> str:
    mapping = {
        "amazing": "🚀 Amazing",
        "good": "👌 Good",
        "neutral": "😐 Neutral",
        "barf": "🤢 Barf",
        "unreviewed": "🙂 Unreviewed",
    }
    return mapping.get(rating_value, "🙂 Unreviewed")


def suggest_combos(base_df: pd.DataFrame, pool_df: pd.DataFrame, mood: str, top_n: int = 12):
    results = []
    seen = set()

    for i, row_a in base_df.iterrows():
        for j, row_b in pool_df.iterrows():
            if row_a["display_name"] == row_b["display_name"]:
                continue

            key = tuple(sorted([row_a["display_name"], row_b["display_name"]]))
            if key in seen:
                continue
            seen.add(key)

            score = combo_score(row_a, row_b, mood)
            results.append({
                "a": row_a,
                "b": row_b,
                "score": score,
                "combo_name": combo_name(row_a, row_b),
                "description": combo_description(row_a, row_b),
                "key": f"{key[0]}|||{key[1]}"
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


# ---------------------------
# Load data and initialize state
# ---------------------------

df = load_fragrances()

if "my_collection" not in st.session_state:
    st.session_state.my_collection = []

if "sniff_list" not in st.session_state:
    st.session_state.sniff_list = []

if "combo_ratings" not in st.session_state:
    st.session_state.combo_ratings = {}

if "selected_result_keys" not in st.session_state:
    st.session_state.selected_result_keys = []


# ---------------------------
# Header
# ---------------------------

st.title("🧪 SniffLab")
st.subheader("Discover your next fragrance combo")
st.caption("Build your collection, sniff for layering ideas, and discover what to try next.")

# ---------------------------
# Sidebar: My Collection
# ---------------------------

with st.sidebar:
    st.header("My Collection")

    if st.session_state.my_collection:
        collection_df = df[df["display_name"].isin(st.session_state.my_collection)].copy()

        if not collection_df.empty:
            families = ["Gourmand", "Floral", "Fresh", "Woody / Warm", "Fruity", "Other"]
            family_icons = {
                "Gourmand": "🧁",
                "Floral": "🌸",
                "Fresh": "🍋",
                "Woody / Warm": "🪵",
                "Fruity": "🍒",
                "Other": "🧪",
            }

            for family in families:
                subset = collection_df[collection_df["family"] == family]
                if subset.empty:
                    continue
                st.markdown(f"**{family_icons.get(family, '🧪')} {family}**")
                for _, row in subset.sort_values("display_name").iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(row["display_name"])
                    if c2.button("✕", key=f"remove_{row['display_name']}"):
                        st.session_state.my_collection = [
                            x for x in st.session_state.my_collection if x != row["display_name"]
                        ]
                        st.rerun()

        st.divider()
        if st.button("Clear My Collection"):
            st.session_state.my_collection = []
            st.rerun()
    else:
        st.info("Your collection is empty.")

    st.divider()
    st.header("Sniff List")

    if st.session_state.sniff_list:
        for item in st.session_state.sniff_list:
            c1, c2 = st.columns([4, 1])
            c1.write(item)
            if c2.button("✕", key=f"remove_sniff_{item}"):
                st.session_state.sniff_list = [x for x in st.session_state.sniff_list if x != item]
                st.rerun()
    else:
        st.caption("No saved wishlist items yet.")

    st.divider()
    st.caption("As an Amazon Associate I earn from qualifying purchases.")


# ---------------------------
# Search + Add to Collection
# ---------------------------

st.markdown("## Add fragrances to My Collection")

brand_values = sorted(df["brand_pretty"].dropna().unique().tolist())
brand_filter = st.selectbox("Filter by brand", ["All Brands"] + brand_values, index=0)

search_query = st.text_input("Search fragrance, brand, notes, or accords", placeholder="Try: desmirage, vanilla, cherry, citrus...")

filtered_df = df.copy()

if brand_filter != "All Brands":
    filtered_df = filtered_df[filtered_df["brand_pretty"] == brand_filter]

if search_query.strip():
    q = search_query.strip().lower()
    filtered_df = filtered_df[filtered_df["search_text"].str.contains(q, na=False)]

# Sort so desmirage appears nicely near the top, then by popularity, then name
filtered_df["brand_priority"] = filtered_df["Brand"].str.lower().apply(lambda x: 0 if x == "desmirage" else 1)
filtered_df = filtered_df.sort_values(
    by=["brand_priority", "rating_count_num", "display_name"],
    ascending=[True, False, True]
)

search_results = filtered_df.head(50)

if search_results.empty:
    st.warning("No fragrances matched that search.")
else:
    st.caption(f"Showing {len(search_results)} result(s)")
    for _, row in search_results.iterrows():
        c1, c2 = st.columns([5, 1])
        c1.write(f"**{row['display_name']}**")
        if c2.button("Add", key=f"add_{row['display_name']}"):
            if row["display_name"] not in st.session_state.my_collection:
                st.session_state.my_collection.append(row["display_name"])
                st.rerun()

# ---------------------------
# Missing fragrance submission
# ---------------------------

with st.expander("Missing a fragrance? Add it for yourself and submit it later"):
    st.caption("This does not add it to the official catalog yet. It is just a placeholder for planning.")
    missing_name = st.text_input("Fragrance name", key="missing_name")
    missing_brand = st.text_input("Brand", key="missing_brand")
    missing_notes = st.text_input("Notes", key="missing_notes")
    if st.button("Save missing fragrance to Sniff List"):
        if missing_name.strip():
            label = f"{missing_name.strip().title()} — {missing_brand.strip().title() if missing_brand.strip() else 'Unknown Brand'}"
            if label not in st.session_state.sniff_list:
                st.session_state.sniff_list.append(label)
            st.success("Added to Sniff List.")
        else:
            st.warning("Enter at least a fragrance name.")


# ---------------------------
# Sniff Controls
# ---------------------------

st.markdown("## Sniff")

col1, col2, col3 = st.columns(3)

with col1:
    mode = st.radio(
        "Source",
        ["My Collection Only", "My Collection + SniffLab Catalog"],
        horizontal=False
    )

with col2:
    mood = st.selectbox(
        "Mood",
        ["Any", "Gourmand", "Floral", "Fresh", "Woody / Warm", "Fruity"]
    )

with col3:
    rating_filter = st.selectbox(
        "Review filter",
        ["All", "Amazing", "Good", "Neutral", "Barf", "Unreviewed"]
    )

if st.button("Sniff", type="primary"):
    collection_df = df[df["display_name"].isin(st.session_state.my_collection)].copy()

    if collection_df.empty:
        st.warning("Add at least one fragrance to My Collection first.")
    else:
        if mode == "My Collection Only":
            pool_df = collection_df.copy()
        else:
            pool_df = df.copy()

        combos = suggest_combos(collection_df, pool_df, mood=mood, top_n=20)

        st.session_state.selected_result_keys = [c["key"] for c in combos]
        st.session_state.latest_combos = combos

# ---------------------------
# Results
# ---------------------------

if "latest_combos" in st.session_state and st.session_state.latest_combos:
    st.markdown("## Layering Suggestions")

    combos_to_show = []
    for combo in st.session_state.latest_combos:
        current_rating = st.session_state.combo_ratings.get(combo["key"], "unreviewed")

        if rating_filter == "All":
            combos_to_show.append(combo)
        elif rating_filter == "Amazing" and current_rating == "amazing":
            combos_to_show.append(combo)
        elif rating_filter == "Good" and current_rating == "good":
            combos_to_show.append(combo)
        elif rating_filter == "Neutral" and current_rating == "neutral":
            combos_to_show.append(combo)
        elif rating_filter == "Barf" and current_rating == "barf":
            combos_to_show.append(combo)
        elif rating_filter == "Unreviewed" and current_rating == "unreviewed":
            combos_to_show.append(combo)

    if not combos_to_show:
        st.info("No combos matched that review filter.")
    else:
        for idx, combo in enumerate(combos_to_show, start=1):
            a = combo["a"]
            b = combo["b"]
            combo_key = combo["key"]
            saved_rating = st.session_state.combo_ratings.get(combo_key, "unreviewed")

            with st.container(border=True):
                st.markdown(f"### {idx}. {combo['combo_name']}")
                st.write(f"**Layer:** {a['display_name']} + {b['display_name']}")
                st.write(f"**Why it may work:** {combo['description']}")
                st.write(f"**Mood fit score:** {combo['score']}")
                st.write(f"**Current rating:** {rating_to_label(saved_rating)}")

                # Spray guidance
                st.caption("Suggested application: 2 sprays of the heavier/warm scent on chest, 1 spray of the brighter scent on neck or shirt.")

                c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 1])

                if c1.button("🚀", key=f"amazing_{combo_key}"):
                    st.session_state.combo_ratings[combo_key] = "amazing"
                    st.rerun()

                if c2.button("👌", key=f"good_{combo_key}"):
                    st.session_state.combo_ratings[combo_key] = "good"
                    st.rerun()

                if c3.button("😐", key=f"neutral_{combo_key}"):
                    st.session_state.combo_ratings[combo_key] = "neutral"
                    st.rerun()

                if c4.button("🤢", key=f"barf_{combo_key}"):
                    st.session_state.combo_ratings[combo_key] = "barf"
                    st.rerun()

                if c5.button("⭐ Save", key=f"save_combo_{combo_key}"):
                    if b["display_name"] not in st.session_state.sniff_list:
                        st.session_state.sniff_list.append(b["display_name"])
                    st.rerun()

                amazon_query = b["perfume_pretty"]
                amazon_url = amazon_search_link(amazon_query)
                c6.link_button("🛒 Check Price", amazon_url)

                st.caption("Tip: Use My Collection Only for closet-based combos, or switch to SniffLab Catalog to discover what to buy next.")


# ---------------------------
# Quick catalog check
# ---------------------------

with st.expander("Catalog check"):
    total_rows = len(df)
    desmirage_rows = len(df[df["Brand"].str.lower() == "desmirage"])
    st.write(f"Total fragrances loaded: {total_rows}")
    st.write(f"desmirage fragrances loaded: {desmirage_rows}")