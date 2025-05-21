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

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
SPORT = "soccer_epl"

TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Aston Villa": 58,
    "Brentford": 402,
    "Brighton & Hove Albion": 397,
    "Burnley": 328,
    "Chelsea": 61,
    "Crystal Palace": 354,
    "Everton": 62,
    "Fulham": 63,
    "Liverpool": 64,
    "Luton Town": 389,
    "Manchester City": 65,
    "Manchester United": 66,
    "Newcastle United": 67,
    "Nottingham Forest": 351,
    "Sheffield United": 356,
    "Tottenham Hotspur": 73,
    "West Ham United": 563,
    "Wolverhampton Wanderers": 76,
    "AFC Bournemouth": 1044
}

# ================== API FUNCTIONS ================== #
@st.cache_data(ttl=3600)
def get_live_odds():
    """Fetch real-time odds from The Odds API"""
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    """Fetch team match data from Football-Data.org"""
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return None
    
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 20}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Stats Error for {team_name}: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_upcoming_matches(team_name):
    """Fetch upcoming matches for a team"""
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return []
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "SCHEDULED", "limit": 10}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Error fetching upcoming matches for {team_name}: {str(e)}")
        return []

# ================== ANALYTICS FUNCTIONS ================== #
def calculate_poisson_probabilities(home_avg, away_avg):
    """Calculate match probabilities using Poisson distribution"""
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
    """Calculate value betting opportunities"""
    return {
        'home': probabilities[0] - 1/odds['home'],
        'draw': probabilities[1] - 1/odds['draw'],
        'away': probabilities[2] - 1/odds['away']
    }

# ================== ML FUNCTIONS ================== #
def load_ml_artifacts():
    """Load ML model and scaler"""
    try:
        return (
            joblib.load("model.pkl"),
            joblib.load("scaler.pkl")
        )
    except FileNotFoundError:
        st.error("ML artifacts missing! Please train model first")
        return None, None

def predict_with_ai(home_stats, away_stats):
    """Generate AI prediction using ML model"""
    model, scaler = load_ml_artifacts()
    if not model: return None
    
    features = np.array([
        home_stats["avg_goals"],
        away_stats["avg_goals"],
        home_stats["win_rate"],
        away_stats["win_rate"]
    ]).reshape(1, -1)
    
    return model.predict_proba(scaler.transform(features))[0]

# ================== UI HELPER FUNCTIONS ================== #
def format_date(iso_date):
    """Convert ISO date to readable format"""
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, is_home=True):
    """Process raw matches data into statistics"""
    if not matches:
        return {
            "avg_goals": 1.2 if is_home else 0.9,
            "win_rate": 0.5 if is_home else 0.3
        }
    
    goals = []
    wins = 0
    
    for match in matches[-10:]:  # Last 10 matches
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            opponent_goals = match["score"]["fullTime"]["away"]
            is_winner = team_goals > opponent_goals
        else:
            team_goals = match["score"]["fullTime"]["away"]
            opponent_goals = match["score"]["fullTime"]["home"]
            is_winner = team_goals > opponent_goals
        
        goals.append(team_goals)
        wins += 1 if is_winner else 0
    
    return {
        "avg_goals": np.mean(goals) if goals else 0,
        "win_rate": wins/len(matches[-10:]) if matches else 0
    }

def get_match_result(match, team_name):
    home_goals = match["score"]["fullTime"]["home"]
    away_goals = match["score"]["fullTime"]["away"]
    home_team = match["home_team"]
    away_team = match["away_team"]
    
    if home_goals is None or away_goals is None:
        return "N/A"
    
    if team_name == home_team:
        opponent = away_team
        venue = "H"
        if home_goals > away_goals:
            outcome = "Win"
        elif home_goals == away_goals:
            outcome = "Draw"
        else:
            outcome = "Loss"
    else:
        opponent = home_team
        venue = "A"
        if away_goals > home_goals:
            outcome = "Win"
        elif away_goals == home_goals:
            outcome = "Draw"
        else:
            outcome = "Loss"
    
    score = f"{home_goals}-{away_goals}" if venue == "H" else f"{away_goals}-{home_goals}"
    return f"{format_date(match['utcDate'])} | vs {opponent} ({venue}) | {score} | {outcome}"

# ================== MAIN INTERFACE ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")
    
    # Data loading section
    with st.spinner("Loading live odds..."):
        matches = get_live_odds()
    
    if not matches:
        st.warning("No matches available")
        return
    
    # Match selection
    selected_match = st.selectbox(
        "Select Match:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches],
        index=0
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    
    # Team stats processing
    with st.spinner("Analyzing teams..."):
        home_stats = get_team_stats_data(get_team_stats(match["home_team"]), is_home=True)
        away_stats = get_team_stats_data(get_team_stats(match["away_team"]), is_home=False)
    
    # Odds processing
    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] 
                       for o in b["markets"][0]["outcomes"] 
                       if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] 
                       for o in b["markets"][0]["outcomes"] 
                       if o["name"] == "Draw"),
            "away": max(o["price"] for b in match["bookmakers"] 
                       for o in b["markets"][0]["outcomes"] 
                       if o["name"] == match["away_team"])
        }
    except:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}
    
    # Calculations
    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], 
        away_stats["avg_goals"]
    )
    
    value_bets = calculate_value_bets(
        (prob_home, prob_draw, prob_away),
        best_odds
    )
    
    # ================== UI DISPLAY ================== #
    tab1, tab2, tab3, tab4 = st.tabs(["Match Analysis", "Team History", "AI Predictions", "Upcoming Matches"])
    
    with tab1:
        cols = st.columns(3)
        outcomes = [
            ("🏠 Home Win", prob_home, value_bets["home"], best_odds["home"]),
            ("⚖ Draw", prob_draw, value_bets["draw"], best_odds["draw"]),
            ("✈ Away Win", prob_away, value_bets["away"], best_odds["away"])
        ]
        
        for col, (title, prob, value, odds) in zip(cols, outcomes):
            with col:
                st.subheader(title)
                st.metric("Probability", f"{prob*100:.1f}%")
                st.metric("Best Odds", f"{odds:.2f}")
                value_color = "green" if value > 0 else "red"
                st.markdown(f"**Value:** <span style='color:{value_color}'>{(value*100):.1f}%</span>", 
                           unsafe_allow_html=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Last 10 Matches - {match['home_team']}")
            home_matches = get_team_stats(match["home_team"])
            if home_matches:
                for m in reversed(home_matches[-10:]):
                    st.write(get_match_result(m, match["home_team"]))
            else:
                st.write("No recent matches found")
        
        with col2:
            st.subheader(f"Last 10 Matches - {match['away_team']}")
            away_matches = get_team_stats(match["away_team"])
            if away_matches:
                for m in reversed(away_matches[-10:]):
                    st.write(get_match_result(m, match["away_team"]))
            else:
                st.write("No recent matches found")
    
    with tab3:
        if st.button("Generate AI Prediction"):
            with st.spinner("Analyzing..."):
                prediction = predict_with_ai(home_stats, away_stats)
            
            if prediction is not None:
                st.subheader("🤖 AI Prediction Results")
                cols = st.columns(3)
                labels = ["Home Win", "Draw",
