import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
from functools import lru_cache

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
SPORT = "soccer_epl"

# Complete team ID mapping for EPL teams
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
    """Get real-time odds from The Odds API"""
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
        st.error(f"Error fetching odds: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    """Get team-specific statistics from Football-Data.org"""
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return None
    
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 10}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Error fetching stats for {team_name}: {str(e)}")
        return None

# ================== ANALYTICS FUNCTIONS ================== #
def calculate_poisson_probabilities(home_avg, away_avg):
    """Calculate match probabilities using Poisson distribution"""
    home_win, draw, away_win = 0, 0, 0
    for i in range(0, 6):
        for j in range(0, 6):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += p
            elif i == j: draw += p
            else: away_win += p
    return home_win, draw, away_win

def get_best_odds(match, outcome_name):
    """Safely get best odds for a specific outcome"""
    odds = []
    for bookmaker in match.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market["key"] == "h2h":
                for outcome in market["outcomes"]:
                    if outcome["name"] == outcome_name:
                        odds.append(outcome.get("price", 1.0))
    return max(odds) if odds else 1.0

# ================== MACHINE LEARNING ================== #
def predict_with_ai(home_stats, away_stats):
    """Generate AI prediction using ML model"""
    try:
        model = joblib.load("model.pkl")
        scaler = joblib.load("scaler.pkl")
    except FileNotFoundError:
        st.error("AI model files not found. Please ensure model.pkl and scaler.pkl are in the directory.")
        return None
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        return None

    try:
        features = np.array([
            home_stats["avg_goals"],
            away_stats["avg_goals"],
            home_stats["win_rate"],
            away_stats["win_rate"]
        ]).reshape(1, -1)
        
        scaled_features = scaler.transform(features)
        prediction = model.predict_proba(scaled_features)
        return prediction[0]
    except Exception as e:
        st.error(f"Prediction error: {str(e)}")
        return None

# ================== UI & DATA PROCESSING ================== #
def process_team_stats(matches, team_id, is_home=True):
    """Process raw match data into actionable statistics"""
    if not matches or not team_id:
        return {
            "avg_goals": 1.2 if is_home else 0.9,
            "win_rate": 0.5 if is_home else 0.3
        }
    
    filtered_matches = [m for m in matches if 
                       (m["homeTeam"]["id"] == team_id if is_home 
                        else m["awayTeam"]["id"] == team_id)]
    
    if not filtered_matches:
        return {
            "avg_goals": 1.2 if is_home else 0.9,
            "win_rate": 0.5 if is_home else 0.3
        }
    
    goals = []
    wins = []
    for m in filtered_matches:
        if is_home:
            goals.append(m["score"]["fullTime"]["home"])
            wins.append(1 if m["score"]["fullTime"]["home"] > m["score"]["fullTime"]["away"] else 0)
        else:
            goals.append(m["score"]["fullTime"]["away"])
            wins.append(1 if m["score"]["fullTime"]["away"] > m["score"]["fullTime"]["home"] else 0)
    
    return {
        "avg_goals": max(np.mean(goals), 0.1),
        "win_rate": np.mean(wins) if wins else 0.5
    }

def main():
    st.set_page_config(page_title="Advanced Bet Analyzer", layout="wide", page_icon="⚽")
    st.title("🔮 Advanced Bet Analyzer Pro")
    
    # Load data
    matches = get_live_odds()
    
    if not matches:
        st.warning("No matches currently available")
        return
    
    # Match selection
    selected_match = st.selectbox(
        "Select match:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    
    # Team data processing
    home_team = match["home_team"]
    away_team = match["away_team"]
    
    home_stats_raw = get_team_stats(home_team)
    away_stats_raw = get_team_stats(away_team)
    
    home_stats = process_team_stats(
        home_stats_raw,
        TEAM_ID_MAPPING.get(home_team),
        is_home=True
    )
    
    away_stats = process_team_stats(
        away_stats_raw,
        TEAM_ID_MAPPING.get(away_team),
        is_home=False
    )
    
    # Calculate probabilities
    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"],
        away_stats["avg_goals"]
    )
    
    # Get odds
    best_odds = {
        "home": get_best_odds(match, home_team),
        "draw": get_best_odds(match, "Draw"),
        "away": get_best_odds(match, away_team)
    }
    
    # Value calculation
    value_bets = {
        "home": prob_home - (1 / best_odds["home"]),
        "draw": prob_draw - (1 / best_odds["draw"]),
        "away": prob_away - (1 / best_odds["away"])
    }
    
    # ================== UI DISPLAY ================== #
    tab1, tab2, tab3 = st.tabs(["Core Analysis", "Historical Stats", "AI Insights"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader(f"🏠 {home_team}")
            st.metric("Avg Goals (Home)", f"{home_stats['avg_goals']:.2f}")
            st.metric("Win Probability", f"{prob_home*100:.1f}%")
            st.metric("Value Opportunity", 
                     f"{value_bets['home']*100:.1f}%",
                     delta="Valuable" if value_bets['home'] > 0 else "No Value")
        
        with col2:
            st.subheader("⚖ Draw")
            st.metric("Probability", f"{prob_draw*100:.1f}%")
            st.metric("Best Odds", f"{best_odds['draw']:.2f}")
            st.metric("Value Opportunity", 
                     f"{value_bets['draw']*100:.1f}%",
                     delta="Valuable" if value_bets['draw'] > 0 else "No Value")
        
        with col3:
            st.subheader(f"✈ {away_team}")
            st.metric("Avg Goals (Away)", f"{away_stats['avg_goals']:.2f}")
            st.metric("Win Probability", f"{prob_away*100:.1f}%")
            st.metric("Value Opportunity", 
                     f"{value_bets['away']*100:.1f}%",
                     delta="Valuable" if value_bets['away'] > 0 else "No Value")
    
    with tab2:
        st.subheader("📊 Historical Performance")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Last 5 Home Matches - {home_team}**")
            home_matches = [m for m in (home_stats_raw or []) 
                           if m["homeTeam"]["id"] == TEAM_ID_MAPPING.get(home_team)]
            for m in home_matches[-5:]:
                result = f"{m['score']['fullTime']['home']}-{m['score']['fullTime']['away']}"
                date = pd.to_datetime(m['utcDate']).strftime('%d %b %Y')
                st.write(f"- {date}: {result}")
        
        with col2:
            st.write(f"**Last 5 Away Matches - {away_team}**")
            away_matches = [m for m in (away_stats_raw or []) 
                           if m["awayTeam"]["id"] == TEAM_ID_MAPPING.get(away_team)]
            for m in away_matches[-5:]:
                result = f"{m['score']['fullTime']['away']}-{m['score']['fullTime']['home']}"
                date = pd.to_datetime(m['utcDate']).strftime('%d %b %Y')
                st.write(f"- {date}: {result}")
    
    with tab3:
        st.subheader("🤖 AI Prediction Engine")
        if st.button("Generate Prediction"):
            prediction = predict_with_ai(home_stats, away_stats)
            if prediction is not None:
                st.progress(prediction[0], text=f"{home_team} Win: {prediction[0]*100:.1f}%")
                st.progress(prediction[1], text=f"Draw: {prediction[1]*100:.1f}%")
                st.progress(prediction[2], text=f"{away_team} Win: {prediction[2]*100:.1f}%")
            else:
                st.warning("Could not generate prediction")

if __name__ == "__main__":
    main()
