import streamlit as st
import pandas as pd

st.set_page_config(page_title="SniffLab", page_icon="🧪", layout="wide")

@st.cache_data
def load_fragrances():
    df = pd.read_csv("data/fragrances.csv", sep=";", encoding="latin1")

    df["Perfume"] = df["Perfume"].fillna("").astype(str)
    df["Brand"] = df["Brand"].fillna("").astype(str)

    df = df[(df["Perfume"].str.strip() != "") & (df["Brand"].str.strip() != "")].copy()
    df["display_name"] = df["Perfume"].str.replace("-", " ", regex=False).str.title() + " — " + df["Brand"].str.replace("-", " ", regex=False).str.title()

    return df

df = load_fragrances()
fragrance_options = sorted(df["display_name"].unique().tolist())

st.title("🧪 SniffLab")
st.subheader("Discover fragrance layering combinations")
st.write("Welcome to SniffLab!")

st.header("My Collection")

collection = st.multiselect(
    "Select fragrances you own",
    fragrance_options,
    placeholder="Search your fragrances..."
)

if st.button("Sniff"):
    if len(collection) < 2:
        st.warning("Select at least 2 fragrances.")
    else:
        st.success(f"Try layering {collection[0]} + {collection[1]}")