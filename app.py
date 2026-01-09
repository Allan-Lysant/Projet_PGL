import streamlit as st
from src import quant_a, quant_b

st.set_page_config(page_title="Projet Finance PGL", layout="wide")
st.sidebar.title("Navigation")

choix = st.sidebar.radio("Modules", ["Quant A", "Quant B"])

if choix == "Quant A":
    quant_a.run()
elif choix == "Quant B":
    quant_b.run()