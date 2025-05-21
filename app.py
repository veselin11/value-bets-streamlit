import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib
from concurrent.futures import ThreadPoolExecutor

# ================ CONFIGURATION ================= #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

# Мултиезична поддръжка
LANGUAGES = {
    "Български": {
        "select_league": "Избери първенство:",
        "select_match": "Изберете мач:",
        "value": "Стойност",
        "odds": "Коефициент",
        # ... добавени други преводи
    },
    "English": {
        "select_league": "Select league:",
        "select_match": "Select match:",
        "value": "Value",
        "odds": "Odds",
        # ... add other translations
    }
}

SPORTS = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one"
}

TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Barcelona": 81,
    "Bayern Munich": 5,
    "Juventus": 109,
    "Paris Saint-Germain": 524,
    "Manchester City": 65,
    "Real Madrid": 86,
    "Inter": 108,
    "Napoli": 113,
    "Liverpool": 64,
}

HISTORY_FILE = "bet_history.csv"

# ================ IMPROVEMENTS ================= #
def validate_match(match):
    """Подобрена валидация на структурата на мача"""
    required_keys = ['home_team', 'away_team', 'bookmakers', 'id']
    return all(key in match for key in required_keys)

def get_hashed_filename(filename):
    """Криптиране на имената на файлове с история"""
    return hashlib.sha256(filename.encode()).hexdigest() + '.csv'

def calculate_kelly(prob, odds):
    """Критерий на Кели за управление на банкрола"""
    if odds <= 1:
        return 0.0
    return (prob * (odds - 1) - (1 - prob)) / (odds - 1)

# ================ API FUNCTIONS ================= #
@st.cache_data(ttl=3600)
def get_live_odds(sport_key):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
        )
        response.raise_for_status()
        return [m for m in response.json() if validate_match(m)]
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return []
    try:
        with ThreadPoolExecutor() as executor:
            matches_future = executor.submit(
                requests.get,
                f"https://api.football-data.org/v4/teams/{team_id}/matches",
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                params={"status": "FINISHED", "limit": 20}
            )
            h2h_future = executor.submit(
                requests.get,
                f"https://api.football-data.org/v4/teams/{team_id}/matches",
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                params={"status": "FINISHED", "limit": 5, "head2head": True}
            )
            
        matches = matches_future.result().json().get("matches", [])
        h2h = h2h_future.result().json().get("matches", [])
        
        return {
            "last_matches": matches[-10:],
            "h2h": h2h,
            "form": matches[-5:]
        }
    except Exception as e:
        st.error(f"Stats Error for {team_name}: {str(e)}")
        return {}

# ================ ENHANCED ANALYTICS ============== #
def get_extended_stats(matches_data, team_name):
    """Разширена статистика с форма и директен сблъсък"""
    if not matches_data:
        return {}
    
    stats = {
        'goals_scored': [],
        'goals_conceded': [],
        'wins': 0,
        'draws': 0,
        'losses': 0
    }
    
    for match in matches_data.get('last_matches', []):
        is_home = match['homeTeam']['name'] == team_name
        team_goals = match['score']['fullTime']['home' if is_home else 'away']
        opp_goals = match['score']['fullTime']['away' if is_home else 'home']
        
        stats['goals_scored'].append(team_goals)
        stats['goals_conceded'].append(opp_goals)
        
        if team_goals > opp_goals:
            stats['wins'] += 1
        elif team_goals == opp_goals:
            stats['draws'] += 1
        else:
            stats['losses'] += 1
    
    return {
        'avg_scored': np.mean(stats['goals_scored'] if stats['goals_scored'] else 0,
        'avg_conceded': np.mean(stats['goals_conceded']) if stats['goals_conceded'] else 0,
        'form': stats['wins']*3 + stats['draws'],
        'h2h': matches_data.get('h2h', [])
    }

# ================ UI COMPONENTS ================== #
def render_match_comparison(home_stats, away_stats):
    """Интерактивна визуализация на сравнение"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Средно голове (домакин)", 
                 f"{home_stats['avg_scored']:.1f}",
                 f"{home_stats['avg_conceded']:.1f} допускани")
    
    with col2:
        st.write("VS")
        st.write(f"Последни 5 мача:")
        st.write(f"Домакин: {home_stats['form']} точки")
        st.write(f"Гост: {away_stats['form']} точки")
    
    with col3:
        st.metric("Средно голове (гост)", 
                 f"{away_stats['avg_scored']:.1f}",
                 f"{away_stats['avg_conceded']:.1f} допускани")

def render_kelly_calculator():
    """Калкулатор за управление на банкрол"""
    with st.expander("Управление на банкрол (Критерий на Кели)"):
        bankroll = st.number_input("Вашият банкрол (€)", min_value=10, value=1000)
        confidence = st.slider("Ниво на увереност (%)", 1, 100, 50)
        max_stake = st.slider("Максимален залог (%)", 1, 100, 20)
        
        return {
            'bankroll': bankroll,
            'confidence': confidence/100,
            'max_stake': max_stake/100
        }

# ================ MAIN APP ====================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor PRO", layout="wide")
    
    # Мултиезична поддръжка
    lang = st.sidebar.selectbox("Language", list(LANGUAGES.keys()))
    texts = LANGUAGES[lang]
    
    # Настройки
    with st.sidebar:
        st.header(texts['settings'])
        min_odds = st.slider(texts['min_odds'], 1.0, 10.0, 1.5)
        kelly_settings = render_kelly_calculator()
    
    # Основен интерфейс
    st.title("⚽ Smart Betting Analyzer PRO")
    
    # Избор на лига и мач
    league = st.selectbox(texts['select_league'], list(SPORTS.keys()))
    matches = get_live_odds(SPORTS[league])
    
    if not matches:
        st.warning(texts['no_matches'])
        return
    
    selected_match = st.selectbox(texts['select_match'], 
                                [f"{m['home_team']} vs {m['away_team']}" for m in matches])
    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)
    
    # Данни за отборите
    with ThreadPoolExecutor() as executor:
        home_data = executor.submit(get_team_stats, match['home_team']).result()
        away_data = executor.submit(get_team_stats, match['away_team']).result()
    
    home_stats = get_extended_stats(home_data, match['home_team'])
    away_stats = get_extended_stats(away_data, match['away_team'])
    
    # Визуализация
    render_match_comparison(home_stats, away_stats)
    
    # Прогнози и коефициенти
    tab1, tab2, tab3 = st.tabs(["Прогнози", "История", "Live"])
    
    with tab1:
        # Подобрена визуализация...
        
    with tab2:
        # Нова история с криптиране...
        
    with tab3:
        # Live актуализации...
        if st.button("🔄 Актуализирай в реално време"):
            st.experimental_rerun()
            # Имплементация на live данни...

if __name__ == "__main__":
    main()
