import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import poisson
from datetime import datetime, timedelta
from functools import lru_cache

# ================== КОНФИГУРАЦИЯ ================== #
try:
    FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError as e:
    st.error(f"Липсващ ключ: {e}")
    st.stop()

SPORT = "soccer_epl"

TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Aston Villa": 58,
    # ... (всички останали отбори)
}

# ================== ФУНКЦИИ ================== #
@st.cache_data(ttl=3600)
def get_live_odds():
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
            params={"apiKey": ODDS_API_KEY, "regions": "eu"}
        )
        return response.json()
    except Exception as e:
        st.error(f"Грешка: {str(e)}")
        return []

# ================== ИНТЕРФЕЙС ================== #
def main():
    st.set_page_config(page_title="Bet Analyzer Pro", layout="wide")
    st.title("⚽ Advanced Analyzer")
    
    matches = get_live_odds()
    
    if not matches:
        st.warning("Няма активни мачове")
        return
    
    selected_match = st.selectbox("Избери мач:", [f'{m["home_team"]} vs {m["away_team"]}' for m in matches])
    
    try:
        match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    except StopIteration:
        st.error("Грешка при избор")
        return

    # Табове
    tab1, tab2, tab3 = st.tabs(["Основен", "Тенденции", "Сравнения"])
    
    with tab1:
        # Основен анализ
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"🏠 {match['home_team']}")
        with col2:
            st.subheader(f"✈ {match['away_team']}")
    
    with tab2:
        # Тенденции
        st.header("📈 Исторически данни")
        col1, col2 = st.columns(2)
        
        with col1:
            if TEAM_ID_MAPPING.get(match["home_team"]):
                st.write(f"Тенденции за {match['home_team']}")
        
        with col2:
            if TEAM_ID_MAPPING.get(match["away_team"]):
                st.write(f"Тенденции за {match['away_team']}")
    
    with tab3:
        # Сравнения
        st.header("🔍 Сравнение на коефициенти")
        st.write("Тук ще се покажат сравненията...")

if __name__ == "__main__":
    main()
