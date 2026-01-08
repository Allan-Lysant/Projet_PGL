import streamlit as st
import numpy as np
import plotly.graph_objects as go
from .data_loader import load_data

#Available assets 
ASSETS = {
    "Cryptos": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"],
    "US Tech": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"],
    "Indices": ["^GSPC", "^DJI", "^IXIC", "^FCHI"], 
    "Forex": ["EURUSD=X", "GBPUSD=X", "JPY=X"],
    "Commodities": ["GC=F", "CL=F"] 
}

TIMEFRAMES = {
    "1 Jour": "D",
    "1 Semaine": "W",
    "1 Mois": "M",
    "1 Heure": "1h",
    "15 Minutes": "15m"
}

#Maximum Drawdown
def calculate_max_drawdown(series):
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return drawdown.min()

#Sharpe Ratio
def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    mean_return = returns.mean() * 252 
    std_return = returns.std() * np.sqrt(252)
    if std_return == 0: return 0
    return (mean_return - risk_free_rate) / std_return

#RSI 
def compute_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

#Module site
def run():
    st.markdown("## Single Asset Analysis(Quant A)")
    
    with st.expander("🔍 Paramètres de recherche", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            #We choose the category and the asset
            category = st.selectbox("Catégorie", list(ASSETS.keys()))
            default_index = 0
            asset = st.selectbox("Actif", ASSETS[category], index=default_index)
            
            #We can also enter a manual ticker
            use_manual = st.checkbox("Ticker manuel ?")
            if use_manual:
                asset = st.text_input("Enter the name of the asset", value="BTC-USD")

        with col2:
            #We choose the timeframe
            interval_label = st.selectbox("Intervalle (Bougies)", list(TIMEFRAMES.keys()), index=0)
            interval_code = TIMEFRAMES[interval_label]

        with col3:
            #We choose the period
            if interval_code in ['1h', '15m']:
                period_options = ["1d", "5d", "1mo"]
                st.info("⚠️ Intraday limité à 1 mois max")
            else:
                period_options = ["3mo", "6mo", "1y", "2y", "5y", "10y", "max"]
            
            period = st.selectbox("Historique", period_options, index=len(period_options)-3) # Par défaut 2y ou 5d

        strategy_type = st.radio("Stratégie", ["Moyenne Mobile", "RSI Momentum"], horizontal=True)

    #Data Loading
    df = load_data(asset, period=period, interval=interval_code)
    
    if df is not None and not df.empty:
        #Returns calculation
        df['Returns'] = df['Price'].pct_change()
        
        #We execute the strategy
        if strategy_type == "Moyenne Mobile":
            max_window = min(200, len(df)//2) if len(df) > 20 else 10
            ma_window = st.slider("Fenêtre MM", 5, max_window, min(50, max_window))
            
            df['Indicator'] = df['Price'].rolling(ma_window).mean()
            df['Signal'] = np.where(df['Price'] > df['Indicator'], 1, 0)
            
        elif strategy_type == "RSI Momentum":
            rsi_window = st.slider("Fenêtre RSI", 5, 30, 14)
            overbought = st.slider("Seuil Vente", 50, 95, 70)
            oversold = st.slider("Seuil Achat", 5, 50, 30)
            
            df['Indicator'] = compute_rsi(df['Price'], rsi_window)
            df['Signal'] = np.where(df['Indicator'] < oversold, 1, 0)

        #Visualisation
        df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']
        df['Cumul_BH'] = (1 + df['Returns']).cumprod() * 100
        df['Cumul_Strat'] = (1 + df['Strategy_Returns']).cumprod() * 100

        #Graph
        fig = go.Figure()
        #We plot the price and the indicator
        fig.add_trace(go.Scatter(x=df.index, y=df['Price'], name='Prix', line=dict(color='grey', width=1), opacity=0.5))
        if strategy_type == "Moyenne Mobile":
             fig.add_trace(go.Scatter(x=df.index, y=df['Indicator'], name=f'MM {ma_window}', line=dict(color='orange')))
        
        #We plot the results of the strategy
        st.plotly_chart(fig, use_container_width=True)
        
        #Graph performance to compare the strategy vs buy & hold
        st.subheader("Strategy performance vs Buy & Hold")
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(x=df.index, y=df['Cumul_BH'], name='Buy & Hold', line=dict(color='blue')))
        fig_perf.add_trace(go.Scatter(x=df.index, y=df['Cumul_Strat'], name='Strategy', line=dict(color='green')))
        st.plotly_chart(fig_perf, use_container_width=True)

        #KPIs
        perf_strat = df['Cumul_Strat'].iloc[-1] - 100
        perf_bh = df['Cumul_BH'].iloc[-1] - 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Perf. Stratégie", f"{perf_strat:.2f}%", delta=f"{perf_strat - perf_bh:.2f}%")
        c2.metric("Max Drawdown", f"{calculate_max_drawdown(df['Cumul_Strat'])*100:.2f}%")
        c3.metric("Sharpe Ratio", f"{calculate_sharpe_ratio(df['Strategy_Returns']):.2f}")

    else:
        st.error(f"Aucune donnée trouvée pour {asset} sur {period} ({interval_code}). Try a shorter period.")