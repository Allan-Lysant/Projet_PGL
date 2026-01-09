import yfinance as yf
import pandas as pd
from typing import List, Tuple

def download_price_data(
    tickers: List[str],
    start: str = "2015-01-01",
    end: str = None,
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Télécharge les prix de clôture ajustés pour une liste de tickers.
    Renvoie un DataFrame avec colonnes = tickers, index = dates.
    """
    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False
    )
    # yfinance renvoie multiindex si plusieurs champs, on ne garde que Close
    if isinstance(data.columns, pd.MultiIndex):
        data = data["Close"]
    data = data.dropna(how="all")
    return data


def compute_returns(
    prices: pd.DataFrame,
    freq: str = "D"
) -> pd.DataFrame:
    """
    Retourne les rendements log ou simples.
    Ici: rendements simples quotidiens.
    """
    rets = prices.pct_change().dropna()
    return rets


import numpy as np

def simulate_portfolio(returns: pd.DataFrame, weights: List[float]) -> pd.Series:
    """
    Calcule la série temporelle des rendements du portefeuille.
    """
    # Vérification que la somme des poids est égale à 1 (ou 100%)
    w = np.array(weights)
    portfolio_rets = returns.dot(w)
    return portfolio_rets

def get_portfolio_metrics(returns: pd.DataFrame, portfolio_rets: pd.Series):
    """
    Calcule les métriques requises : corrélation, volatilité, etc. 
    """
    metrics = {
        "correlation_matrix": returns.corr(),
        "portfolio_volatility": portfolio_rets.std() * np.sqrt(252), # Volatilité annualisée
        "portfolio_return": portfolio_rets.mean() * 252,             # Rendement annualisé
        "cumulative_returns": (1 + portfolio_rets).cumprod()        # Pour le graphique final [cite: 44]
    }
    return metrics








import streamlit as st
import plotly.express as px

st.title("Module Quant B : Analyse Multi-Assets")

# 1. Sélection des actifs (au moins 3 requis) [cite: 41]
tickers_input = st.multiselect(
    "Choisissez au moins 3 actifs", 
    ["AAPL", "TSLA", "MSFT", "GOOGL", "BTC-USD", "EURUSD=X"],
    default=["AAPL", "MSFT", "BTC-USD"]
)

if len(tickers_input) >= 3:
    # Récupération des données via vos fonctions
    prices = download_price_data(tickers_input)
    returns = compute_returns(prices)
    
    # 2. Paramètres de pondération 
    st.sidebar.header("Pondération du Portefeuille")
    weights = []
    for ticker in tickers_input:
        w = st.sidebar.slider(f"Poids pour {ticker}", 0.0, 1.0, 1.0/len(tickers_input))
        weights.append(w)
    
    # Normalisation des poids pour que la somme = 1
    total_w = sum(weights)
    weights = [w / total_w for w in weights]

    # 3. Calculs
    port_rets = simulate_portfolio(returns, weights)
    metrics = get_portfolio_metrics(returns, port_rets)

    # 4. Affichage du graphique principal [cite: 44]
    # Comparaison prix individuels vs Valeur cumulative du portefeuille
    st.subheader("Performance Cumulative du Portefeuille")
    cum_prices = (1 + returns).cumprod() # Normalisation à 1 pour comparaison
    cum_prices["PORTFOLIO"] = metrics["cumulative_returns"]
    
    fig = px.line(cum_prices, title="Comparaison Actifs vs Portefeuille")
    st.plotly_chart(fig)

    # 5. Matrice de corrélation 
    st.subheader("Analyse de Diversification")
    fig_corr = px.imshow(metrics["correlation_matrix"], text_auto=True, title="Matrice de Corrélation")
    st.plotly_chart(fig_corr)
    
    # Affichage des métriques clés
    col1, col2 = st.columns(2)
    col1.metric("Rendement Annuel", f"{metrics['portfolio_return']:.2%}")
    col2.metric("Volatilité Annuelle", f"{metrics['portfolio_volatility']:.2%}")
else:
    st.warning("Veuillez sélectionner au moins 3 actifs pour activer le module Quant B[cite: 41].")