import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import os

ASSET = "BTC-USD"  
REPORT_DIR = "reports"

def calculate_max_drawdown(series):
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return drawdown.min()

def generate_report():
    print(f"Récupération des données pour {ASSET}...")
    df = yf.download(ASSET, period="1y", interval="1d", progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs('Close', axis=1, level=0, drop_level=True)
    else:
        df = df[['Close']]
    df.columns = ['Price']

    last_price = df['Price'].iloc[-1]
    open_price = df['Price'].iloc[-1] 
    returns = df['Price'].pct_change()
    
    #Volatility
    volatility = returns.std() * np.sqrt(252) * 100
    
    #Max Drawdown
    max_dd = calculate_max_drawdown((1 + returns).cumprod()) * 100

    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_content = f"""
    === RAPPORT QUOTIDIEN : {ASSET} ===
    Date : {today}
    
    Prix de Clôture : {last_price:.2f} $
    Volatilité (Ann) : {volatility:.2f}%
    Max Drawdown (1Y): {max_dd:.2f}%
    ===================================
    """
    
    #We save the file
    filename = f"{REPORT_DIR}/report_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
    os.makedirs(REPORT_DIR, exist_ok=True) # Create dir if not exists
    
    with open(filename, "w") as f:
        f.write(report_content)
    
    print(f"Rapport généré avec succès : {filename}")

if __name__ == "__main__":
    generate_report()