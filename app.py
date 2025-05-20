import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta

# ================== CONFIGURATION ==================

FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
SPORT = "soccer_epl"

TEAM_ID_MAPPING = {
    "Arsenal": 57, "Aston Villa": 58, "Brentford": 402, "Brighton & Hove Albion": 397,
    "Burnley": 328, "Chelsea": 61, "Crystal Palace": 354, "Everton": 62,
    "Fulham": 63, "Liverpool": 64, "Luton Town": 389, "Manchester City": 65,
    "Manchester United": 66, "Newcastle United": 67, "Nottingham Forest": 351,
    "Sheffield United": 356, "Tottenham Hotspur": 73, "West Ham United": 563,
    "Wolverhampton Wanderers": 76, "AFC Bournemouth": 1044
}

# ================== API FUNCTIONS ==================

@st.cache_data(ttl=3600)
def get_live_odds(date_from, date_to):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "commenceTimeFrom": date_from,
                "commenceTimeTo": date_to
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

# ================== DATE HANDLING ==================

def get_date_range(selected_date):
    start = datetime.combine(selected_date, datetime.min.time()).isoformat() + "Z"
    end = datetime.combine(selected_date + timedelta(days=1), datetime.min.time()).isoformat() + "Z"
    return start, end

# ================== ANALYTICS FUNCTIONS ================== 
# (Остават същите като в предишната версия)
# ================== ML FUNCTIONS ==================
# (Остават същите като в предишната версия)
# ================== UI HELPER FUNCTIONS ==================
# (Остават същите като в предишната версия)

# ================== MAIN INTERFACE ==================

def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")
    
    # Дата селектор
    col_date, _ = st.columns([0.2, 0.8])
    with col_date:
        selected_date = st.date_input(
            "📅 Select Match Date",
            datetime.today(),
            min_value=datetime.today() - timedelta(days=7),
            max_value=datetime.today() + timedelta(days=365)
        )
    
    # Генериране на дати за API заявка
    date_from, date_to = get_date_range(selected_date)
    
    # Зареждане на мачове
    with st.spinner(f"🔍 Loading matches for {selected_date.strftime('%d %b %Y')}..."):
        matches = get_live_odds(date_from, date_to)

    if not matches:
        st.warning(f"⚠️ No matches found for {selected_date.strftime('%d %b %Y')}")
        return

    try:
        match_options = [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
        selected_match = st.selectbox("⚽ Select Match:", match_options)
        match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    except StopIteration:
        st.error("❌ Selected match not found")
        return

    # Останалата логика остава същата
    with st.spinner("📊 Analyzing teams..."):
        home_stats = get_team_stats_data(get_team_stats(match["home_team"]) or [], is_home=True)
        away_stats = get_team_stats_data(get_team_stats(match["away_team"]) or [], is_home=False)

    # ... (останалият код остава непроменен) ...

if __name__ == "__main__":
    main()
