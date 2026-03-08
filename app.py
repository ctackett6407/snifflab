import streamlit as st

st.set_page_config(page_title="SniffLab", page_icon="🧪", layout="wide")

st.title("🧪 SniffLab")
st.subheader("Discover fragrance layering combinations")

st.write("Welcome to SniffLab!")

st.header("My Collection")

collection = st.multiselect(
    "Select fragrances you own",
    ["Example Fragrance 1", "Example Fragrance 2"]
)

if st.button("Sniff"):
    st.success("Layer Example Fragrance 1 + Example Fragrance 2")
