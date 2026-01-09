import streamlit as st
try:
    from src import quant_a
except ImportError:
    quant_a = None

st.set_page_config(page_title="Projet Finance", layout="wide")
st.title("Dashboard Financier")

module = st.sidebar.radio("Module", ["Quant A", "Quant B"])

if module == "Quant A":
    if quant_a:
        quant_a.run()
    else:
        st.error("Le fichier src/quant_a.py est introuvable.")
        
elif module == "Quant B":
    st.info("🚧 Module Quant B en construction par le binôme.")