import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from .data_loader import load_data

#Max Drawdown
def calculate_max_drawdown(series):
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return drawdown.min()
#Sharpe Ratio
def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    mean_return = returns.mean() * 252 
    std_return = returns.std() * np.sqrt(252)
    if std_return == 0:
        return 0
    return (mean_return - risk_free_rate) / std_return
#RSI
def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run():
    st.markdown("## 📊 Analyse Univariée & Backtesting (Quant A)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        asset = st.text_input("Actif (Yahoo Ticker)", value="BTC-USD")
    with col2:
        period = st.selectbox("Période", ["6mo", "1y", "2y", "5y"], index=1)
    with col3:
        strategy_type = st.selectbox("Stratégie à tester", ["Moyenne Mobile", "RSI Momentum"])

    df = load_data(asset, period=period) #Data loading
    
    if df is not None:
        df['Returns'] = df['Price'].pct_change() #Returns computation
        if strategy_type == "Moyenne Mobile":
            st.markdown("#### Paramètres Moyenne Mobile")
            ma_window = st.slider("Fenêtre (Jours)", 10, 200, 50)

            df['Indicator'] = df['Price'].rolling(ma_window).mean()
 
            df['Signal'] = np.where(df['Price'] > df['Indicator'], 1, 0) #We buy if Price > MA
            
        elif strategy_type == "RSI Momentum":
            st.markdown("#### Paramètres RSI")
            rsi_window = st.slider("Fenêtre RSI", 5, 30, 14)
            rsi_overbought = st.slider("Seuil Surachat (Vente)", 50, 90, 70)
            rsi_oversold = st.slider("Seuil Survente (Achat)", 10, 50, 30)

            df['Indicator'] = compute_rsi(df['Price'], rsi_window)
            df['Signal'] = np.where(df['Indicator'] < rsi_oversold, 1, 0)

        df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']
        

        df['Cumul_BH'] = (1 + df['Returns']).cumprod() * 100
        df['Cumul_Strat'] = (1 + df['Strategy_Returns']).cumprod() * 100

        st.markdown("### 🏆 Performance vs Buy & Hold")
        
        bh_perf = (df['Cumul_BH'].iloc[-1] - 100)
        strat_perf = (df['Cumul_Strat'].iloc[-1] - 100)
        
        sharpe_bh = calculate_sharpe_ratio(df['Returns'])
        sharpe_strat = calculate_sharpe_ratio(df['Strategy_Returns'])
        
        dd_bh = calculate_max_drawdown(df['Cumul_BH']) * 100
        dd_strat = calculate_max_drawdown(df['Cumul_Strat']) * 100


        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rendement Total", f"{strat_perf:.2f}%", delta=f"{strat_perf - bh_perf:.2f}% vs B&H")
        m2.metric("Sharpe Ratio", f"{sharpe_strat:.2f}", delta=f"{sharpe_strat - sharpe_bh:.2f}")
        m3.metric("Max Drawdown", f"{dd_strat:.2f}%", delta=f"{dd_strat - dd_bh:.2f}% (inv)")
        m4.metric("Volatilité", f"{df['Strategy_Returns'].std()*np.sqrt(252)*100:.2f}%")

        #Graphique
        st.markdown("### 📈 Évolution du Portefeuille")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Cumul_BH'], mode='lines', name='Buy & Hold'))
        fig.add_trace(go.Scatter(x=df.index, y=df['Cumul_Strat'], mode='lines', name=f'Stratégie {strategy_type}'))
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Voir les données détaillées"):
            st.dataframe(df.tail(50))