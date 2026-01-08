import streamlit as st
import numpy as np
import plotly.graph_objects as go
from .data_loader import load_data

#Assets 
ASSETS = {
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"],
    "US Tech": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"],
    "Indices": ["^GSPC", "^DJI", "^IXIC", "^FCHI"], # S&P500, Dow, Nasdaq, CAC40
    "Forex": ["EURUSD=X", "GBPUSD=X", "JPY=X"],
    "Commodities": ["GC=F", "CL=F"] # Gold, Crude Oil
}

#Timeframes
TIMEFRAMES = {
    "D": "1d",
    "W": "1wk",
    "M": "1mo",
    "1H": "1h",
    "15m": "15m"
}

#Maximum Drawdown
def calculate_max_drawdown(series):
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return drawdown.min()

#Sharpe Ratio
def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    # Annualized adjustment (252 days approx for daily data)
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
    st.markdown("## Single Asset Analysis (Quant A)")
    
    with st.expander("Search Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            #We chosse the category and the asset
            category = st.selectbox("Category", list(ASSETS.keys()))
            default_index = 0
            asset = st.selectbox("Asset", ASSETS[category], index=default_index)
            
            #We can also enter manually the ticker
            use_manual = st.checkbox("Manual Ticker?")
            if use_manual:
                asset = st.text_input("Enter Yahoo Symbol", value="BTC-USD")

        with col2:
            #We choose the timeframe
            timeframe_label = st.selectbox("Timeframe", list(TIMEFRAMES.keys()), index=0)
            timeframe_code = TIMEFRAMES[timeframe_label]

        with col3:
            #We choose the history period
            if timeframe_code in ['1h', '15m']:
                period_options = ["1d", "5d", "1mo"]
                st.info("⚠️ Intraday limited to 1 month max")
            else:
                period_options = ["3mo", "6mo", "1y", "2y", "5y", "10y", "max"]
            
            period = st.selectbox("History Period", period_options, index=len(period_options)-3) # Default 2y or 5d

        strategy_type = st.radio("Strategy", ["Moving Average", "RSI Momentum"], horizontal=True)

    #Data Loading
    df = load_data(asset, period=period, interval=timeframe_code)
    
    if df is not None and not df.empty:
        #Returns Calculation
        df['Returns'] = df['Price'].pct_change()
        
        #We execute the strategy
        if strategy_type == "Moving Average":
            max_window = min(200, len(df)//2) if len(df) > 20 else 10
            ma_window = st.slider("MA Window", 5, max_window, min(50, max_window))
            
            df['Indicator'] = df['Price'].rolling(ma_window).mean()
            df['Signal'] = np.where(df['Price'] > df['Indicator'], 1, 0)
            
        elif strategy_type == "RSI Momentum":
            rsi_window = st.slider("RSI Window", 5, 30, 14)
            overbought = st.slider("Overbought Level", 50, 95, 70)
            oversold = st.slider("Oversold Level", 5, 50, 30)
            
            df['Indicator'] = compute_rsi(df['Price'], rsi_window)
            df['Signal'] = np.where(df['Indicator'] < oversold, 1, 0)

        #Visualisation
        df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']
        df['Cumul_BH'] = (1 + df['Returns']).cumprod() * 100
        df['Cumul_Strat'] = (1 + df['Strategy_Returns']).cumprod() * 100

        #Chart
        fig = go.Figure()
        #We plot the price and the indicator
        fig.add_trace(go.Scatter(x=df.index, y=df['Price'], name='Price', line=dict(color='grey', width=1), opacity=0.5))
        if strategy_type == "Moving Average":
             fig.add_trace(go.Scatter(x=df.index, y=df['Indicator'], name=f'MA {ma_window}', line=dict(color='orange')))
        
        st.plotly_chart(fig, use_container_width=True)
        
        #Chart performance to compare the stratgey vs Buy & Hold
        st.subheader("Strategy vs Benchmark Performance")
        fig_perf = go.Figure()
        fig_perf.add_trace(go.Scatter(x=df.index, y=df['Cumul_BH'], name='Buy & Hold', line=dict(color='blue')))
        fig_perf.add_trace(go.Scatter(x=df.index, y=df['Cumul_Strat'], name='Strategy', line=dict(color='green')))
        st.plotly_chart(fig_perf, use_container_width=True)

        #KPIs 
        perf_strat = df['Cumul_Strat'].iloc[-1] - 100
        perf_bh = df['Cumul_BH'].iloc[-1] - 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Return", f"{perf_strat:.2f}%", delta=f"{perf_strat - perf_bh:.2f}%")
        c2.metric("Max Drawdown", f"{calculate_max_drawdown(df['Cumul_Strat'])*100:.2f}%")
        c3.metric("Sharpe Ratio", f"{calculate_sharpe_ratio(df['Strategy_Returns']):.2f}")

    else:
        st.error(f"No data found for {asset} over {period} ({timeframe_code}). Try a shorter period for intraday data.")