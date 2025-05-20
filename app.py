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

DEFAULT_TEAM_ID_MAPPING = {
    "Arsenal": 57, "Aston Villa": 58, "Brentford": 402, "Brighton & Hove Albion": 397,
    "Burnley": 328, "Chelsea": 61, "Crystal Palace": 354, "Everton": 62,
    "Fulham": 63, "Liverpool": 64, "Luton Town": 389, "Manchester City": 65,
    "Manchester United": 66, "Newcastle United": 67, "Nottingham Forest": 351,
    "Sheffield United": 356, "Tottenham Hotspur": 73, "West Ham United": 563,
    "Wolverhampton Wanderers": 76, "AFC Bournemouth": 1044
}

@st.cache_data(ttl=86400)
def load_team_id_mapping():
    try:
        response = requests.get(
            "https://api.football-data.org/v4/competitions/PL/teams",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY}
        )
        response.raise_for_status()
        data = response.json()
        mapping = {team["name"]: team["id"] for team in data["teams"]}
        if mapping:
            return mapping
        else:
            st.warning("Empty team list from API, using default mapping.")
            return DEFAULT_TEAM_ID_MAPPING
    except Exception as e:
        st.warning(f"Failed to load teams from API ({e}), using default mapping.")
        return DEFAULT_TEAM_ID_MAPPING

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
def calculate_poisson_probabilities(home_avg, away_avg):
    max_goals = 10
    home_win, draw, away_win = 0, 0, 0

    for i in range(max_goals):
        for j in range(max_goals):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += p
            elif i == j: draw += p
            else: away_win += p

    total = home_win + draw + away_win
    return home_win/total, draw/total, away_win/total

def calculate_value_bets(probabilities, odds):
    return {
        'home': (probabilities[0] * odds['home']) - 1,
        'draw': (probabilities[1] * odds['draw']) - 1,
        'away': (probabilities[2] * odds['away']) - 1
    }

# ================== ML FUNCTIONS ==================
def load_ml_artifacts():
    try:
        return (joblib.load("model.pkl"), joblib.load("scaler.pkl"))
    except FileNotFoundError:
        st.error("ML artifacts missing! Please train model first.")
        return None, None

def predict_with_ai(home_stats, away_stats):
    model, scaler = load_ml_artifacts()
    if not model: return None

    features = np.array([
        home_stats["avg_goals"],
        away_stats["avg_goals"],
        home_stats["win_rate"],
        away_stats["win_rate"]
    ]).reshape(1, -1)

    return model.predict_proba(scaler.transform(features))[0]

# ================== UI HELPER FUNCTIONS ==================
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, team_name):
    if not matches:
        return {"avg_goals": 1.2, "win_rate": 0.5}  # Default values
    
    goals = []
    wins = 0

    for match in matches[-10:]:
        try:
            is_home = match["homeTeam"]["name"] == team_name
            score = match["score"]["fullTime"]
            
            team_goals = score["home"] if is_home else score["away"]
            opp_goals = score["away"] if is_home else score["home"]
            
            goals.append(team_goals)
            if team_goals > opp_goals:
                wins += 1
        except KeyError:
            continue

    avg_goals = np.mean(goals) if goals else 0
    win_rate = wins/len(goals) if goals else 0

    return {"avg_goals": avg_goals, "win_rate": win_rate}

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        st.warning(f"No team ID found for {team_name}. Using default stats.")
        return []
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 10}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Error fetching matches for {team_name}: {str(e)}")
        return []

# ================== MAIN INTERFACE ==================
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    global TEAM_ID_MAPPING
    TEAM_ID_MAPPING = load_team_id_mapping()

    if not TEAM_ID_MAPPING:
        st.error("No team mapping available. Cannot continue.")
        return
    
    # Date selector
    col_date, _ = st.columns([0.2, 0.8])
    with col_date:
        selected_date = st.date_input(
            "📅 Select Match Date",
            datetime.today(),
            min_value=datetime.today() - timedelta(days=7),
            max_value=datetime.today() + timedelta(days=365)
        )
    
    # Generate date range
    date_from, date_to = get_date_range(selected_date)
    
    # Load matches
    with st.spinner(f"🔍 Loading matches for {selected_date.strftime('%d %b %Y')}..."):
        matches = get_live_odds(date_from, date_to)

    if not matches:
        st.warning(f"⚠️ No matches found for {selected_date.strftime('%d %b %Y')}")
        return

    # Match selection
    try:
        match_options = [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
        selected_match = st.selectbox("⚽ Select Match:", match_options)
        match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    except StopIteration:
        st.error("❌ Selected match not found")
        return

    # Team analysis
    with st.spinner("📊 Analyzing teams..."):
        home_team = match["home_team"]
        away_team = match["away_team"]

        if home_team not in TEAM_ID_MAPPING or away_team not in TEAM_ID_MAPPING:
            st.warning("Team ID not found for one or both teams. Using default stats.")
            home_matches, away_matches = [], []
        else:
            home_matches = get_team_stats(home_team) or []
            away_matches = get_team_stats(away_team) or []

        home_stats = get_team_stats_data(home_matches, home_team)
        away_stats = get_team_stats_data(away_matches, away_team)

    # Тук можеш да добавиш следващата си логика - AI прогноза, poisson, value bets и др.
    # ...

if __name__ == "__main__":
    main()
