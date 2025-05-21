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

LANGUAGES = {
    "Български": {
        "select_league": "Избери първенство:",
        "select_match": "Изберете мач:",
        "value": "Стойност",
        "odds": "Коефициент",
        "no_matches": "Няма налични мачове.",
        "settings": "Настройки",
        "min_odds": "Минимален коефициент",
    },
    "English": {
        "select_league": "Select league:",
        "select_match": "Select match:",
        "value": "Value",
        "odds": "Odds",
        "no_matches": "No matches available.",
        "settings": "Settings",
        "min_odds": "Minimum odds",
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
    return all(key in match for key in ['home_team', 'away_team', 'bookmakers', 'id'])

def get_hashed_filename(filename):
    return hashlib.sha256(filename.encode()).hexdigest() + '.csv'

def calculate_kelly(prob, odds):
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
        return {}
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
                params={"status": "FINISHED", "limit": 5, "head2head": "true"}
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
        'avg_scored': np.mean(stats['goals_scored']) if stats['goals_scored'] else 0,
        'avg_conceded': np.mean(stats['goals_conceded']) if stats['goals_conceded'] else 0,
        'form': stats['wins']*3 + stats['draws'],
        'h2h': matches_data.get('h2h', [])
    }

def calculate_poisson_probabilities(home_avg, away_avg):
    max_goals = 10
    home_win, draw, away_win = 0, 0, 0
    for i in range(max_goals):
        for j in range(max_goals):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p
    total = home_win + draw + away_win
    return home_win/total, draw/total, away_win/total

# ================ UI COMPONENTS ================== #
def render_match_comparison(home_stats, away_stats, texts):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(f"{texts['avg_goals']} (Home)", 
                 f"{home_stats['avg_scored']:.1f}",
                 f"{home_stats['avg_conceded']:.1f} {texts['conceded']}")

    with col2:
        st.write("VS")
        st.write(f"{texts['last_5']}:")
        st.write(f"{texts['home']}: {home_stats['form']} {texts['points']}")
        st.write(f"{texts['away']}: {away_stats['form']} {texts['points']}")

    with col3:
        st.metric(f"{texts['avg_goals']} (Away)", 
                 f"{away_stats['avg_scored']:.1f}",
                 f"{away_stats['avg_conceded']:.1f} {texts['conceded']}")

def render_kelly_calculator(texts):
    with st.expander(texts['kelly_title']):
        bankroll = st.number_input(texts['bankroll'], min_value=10, value=1000)
        confidence = st.slider(texts['confidence'], 1, 100, 50)
        max_stake = st.slider(texts['max_stake'], 1, 100, 20)
        
        return {
            'bankroll': bankroll,
            'confidence': confidence/100,
            'max_stake': max_stake/100
        }

# ================ MAIN APP ====================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor PRO", layout="wide")
    
    lang = st.sidebar.selectbox("Language", list(LANGUAGES.keys()))
    texts = LANGUAGES[lang]
    
    with st.sidebar:
        st.header(texts['settings'])
        min_odds = st.slider(texts['min_odds'], 1.0, 10.0, 1.5)
        kelly_settings = render_kelly_calculator(texts)
    
    st.title("⚽ Smart Betting Analyzer PRO")
    
    league = st.selectbox(texts['select_league'], list(SPORTS.keys()))
    matches = get_live_odds(SPORTS[league])
    
    if not matches:
        st.warning(texts['no_matches'])
        return
    
    selected_match = st.selectbox(
        texts['select_match'],
        [f"{m['home_team']} vs {m['away_team']}" for m in matches]
    )
    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)
    
    with ThreadPoolExecutor() as executor:
        home_data = executor.submit(get_team_stats, match['home_team']).result()
        away_data = executor.submit(get_team_stats, match['away_team']).result()
    
    home_stats = get_extended_stats(home_data, match['home_team'])
    away_stats = get_extended_stats(away_data, match['away_team'])
    
    render_match_comparison(home_stats, away_stats, texts)
    
    tab1, tab2, tab3 = st.tabs([texts['predictions'], texts['history'], texts['live']])
    
    with tab1:
        prob = calculate_poisson_probabilities(home_stats['avg_scored'], away_stats['avg_scored'])
        
        col1, col2, col3 = st.columns(3)
        outcomes = [
            (match['home_team'], prob[0], best_odds['home']),
            ("Draw", prob[1], best_odds['draw']),
            (match['away_team'], prob[2], best_odds['away'])
        ]
        
        for col, (label, probability, odds) in zip([col1, col2, col3], outcomes):
            col.metric(label, f"{probability*100:.1f}%", 
                      delta=f"{texts['value']}: {(probability - 1/odds)*100:.2f}%")
            col.write(f"{texts['odds']}: {odds:.2f}")
            kelly = calculate_kelly(probability, odds)
            col.progress(min(int(kelly*100), 100), f"Kelly: {kelly*100:.1f}%")

    with tab2:
        st.subheader(texts['bet_history'])
        if st.button(texts['refresh_history']):
            st.experimental_rerun()
        
        try:
            history_df = pd.read_csv(get_hashed_filename(HISTORY_FILE))
            st.dataframe(history_df)
        except FileNotFoundError:
            st.info(texts['no_history'])

    with tab3:
        st.subheader(texts['live_updates'])
        if st.button("🔄 " + texts['refresh']):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
