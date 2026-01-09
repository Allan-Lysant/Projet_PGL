import streamlit as st
from src import quant_a, quant_b

st.set_page_config(page_title="Projet Finance PGL", layout="wide")
st.sidebar.title("Navigation")

choix = st.sidebar.radio("Modules", ["Partie A (Moi)", "Partie B (Binôme)"])

if choix == "Partie A (Moi)":
    quant_a.run()
elif choix == "Partie B (Binôme)":
    quant_b.run()