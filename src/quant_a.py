import streamlit as st
import numpy as np
from .data_loader import load_data

def run():
    st.header("📈 Analyse Univariée (Quant A)")
    
    col1, col2 = st.columns(2)
    asset = col1.text_input("Actif", "BTC-USD")
    ma_window = col2.slider("Moyenne Mobile (Jours)", 10, 200, 50)
    
    df = load_data(asset)
    if df is not None:
        df['Returns'] = df['Price'].pct_change()
        df['MA'] = df['Price'].rolling(ma_window).mean()
        df['Signal'] = np.where(df['Price'] > df['MA'], 1, 0)
        df['Strat_Ret'] = df['Signal'].shift(1) * df['Returns']
        
        df['Cumul_BH'] = (1 + df['Returns']).cumprod()
        df['Cumul_Strat'] = (1 + df['Strat_Ret']).cumprod()
        
        st.line_chart(df[['Cumul_BH', 'Cumul_Strat']])
        
        perf = (df['Cumul_Strat'].iloc[-1] - 1) * 100
        st.metric("Performance Stratégie", f"{perf:.2f}%")