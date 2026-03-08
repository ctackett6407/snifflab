import os

base_path = r"C:\snifflab\snifflab"

folders = [
    "data",
    "utils",
    "assets"
]

files = {
    "app.py": """import streamlit as st

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
""",

    "requirements.txt": """streamlit
pandas
numpy
""",

    "data/fragrances.csv": """id,name,brand,source,top_notes,middle_notes,base_notes,accords
1,Example Fragrance 1,DemoBrand,curated,bergamot,jasmine,amber,amber sweet
2,Example Fragrance 2,DemoBrand,curated,lemon,rose,vanilla,floral sweet
""",

    "data/combos.csv": """combo_id,fragrance_a,fragrance_b,mood,description
1,Example Fragrance 1,Example Fragrance 2,random,Test combo
""",

    "utils/combo_engine.py": """def generate_combo(collection):
    if len(collection) >= 2:
        return f"Try layering {collection[0]} + {collection[1]}"
    return "Add more fragrances to your collection."
""",

    "utils/data_loader.py": """import pandas as pd

def load_fragrances(path):
    return pd.read_csv(path)
"""
}

# Create folders
for folder in folders:
    os.makedirs(os.path.join(base_path, folder), exist_ok=True)

# Create files
for path, content in files.items():
    full_path = os.path.join(base_path, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("SniffLab project structure created successfully!")