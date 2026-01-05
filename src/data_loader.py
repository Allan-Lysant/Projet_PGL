import yfinance as yf
import pandas as pd
import streamlit as st

def load_data(ticker, period="1y", interval="1d"):
    @st.cache_data(ttl=300)
    def fetch(t, p, i):
        return yf.download(t, period=p, interval=i, progress=False)

    try:
        df = fetch(ticker, period, interval)
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs('Close', axis=1, level=0, drop_level=True)
        else:
            df = df[['Close']]
            
        df.columns = ['Price']
        return df
    except Exception as e:
        st.error(f"Erreur: {e}")
        return None