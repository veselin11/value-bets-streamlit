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

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        st.error(f"Team ID not found for {team_name}")
        return []
    
    try:
        url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
        headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        matches = response.json()["matches"]
        completed_matches = [m for m in matches if m["status"] == "FINISHED"]
        return completed_matches
    except Exception as e:
        st.error(f"Football Data API Error: {str(e)}")
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
    win_rate = wins/len(matches[-10:]) if len(matches) >= 10 else wins/len(matches) if matches else 0

    return {"avg_goals": avg_goals or 1.2, "win_rate": win_rate or 0.5}

# ================== MAIN INTERFACE ==================
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")
    
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
        
        home_matches = get_team_stats(home_team) or []
        away_matches = get_team_stats(away_team) or []
        
        home_stats = get_team_stats_data(home_matches, home_team)
        away_stats = get_team_stats_data(away_matches, away_team)

    # Calculate probabilities
    poisson_probs = calculate_poisson_probabilities(home_stats["avg_goals"], away_stats["avg_goals"])
    ai_probs = predict_with_ai(home_stats, away_stats)

    # Get best odds
    best_odds = {'home': 0, 'draw': 0, 'away': 0}
    for bookmaker in match.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market['key'] == 'h2h':
                for outcome in market['outcomes']:
                    if outcome['name'] == home_team:
                        if outcome['price'] > best_odds['home']:
                            best_odds['home'] = outcome['price']
                    elif outcome['name'] == 'Draw':
                        if outcome['price'] > best_odds['draw']:
                            best_odds['draw'] = outcome['price']
                    elif outcome['name'] == away_team:
                        if outcome['price'] > best_odds['away']:
                            best_odds['away'] = outcome['price']

    # Calculate value bets
    poisson_value = calculate_value_bets(poisson_probs, best_odds)
    ai_value = calculate_value_bets(ai_probs, best_odds) if ai_probs else None

    # Display results
    st.subheader("📈 Prediction Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Poisson Home Win", f"{poisson_probs[0]*100:.1f}%", 
                 delta=f"Value: {poisson_value['home']:.2f}" if poisson_value['home'] > 0 else None)
    with col2:
        st.metric("Poisson Draw", f"{poisson_probs[1]*100:.1f}%",
                 delta=f"Value: {poisson_value['draw']:.2f}" if poisson_value['draw'] > 0 else None)
    with col3:
        st.metric("Poisson Away Win", f"{poisson_probs[2]*100:.1f}%",
                 delta=f"Value: {poisson_value['away']:.2f}" if poisson_value['away'] > 0 else None)

    if ai_probs is not None:
        st.subheader("🤖 AI Prediction")
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("AI Home Win", f"{ai_probs[0]*100:.1f}%",
                     delta=f"Value: {ai_value['home']:.2f}" if ai_value and ai_value['home'] > 0 else None)
        with col5:
            st.metric("AI Draw", f"{ai_probs[1]*100:.1f}%",
                     delta=f"Value: {ai_value['draw']:.2f}" if ai_value and ai_value['draw'] > 0 else None)
        with col6:
            st.metric("AI Away Win", f"{ai_probs[2]*100:.1f}%",
                     delta=f"Value: {ai_value['away']:.2f}" if ai_value and ai_value['away'] > 0 else None)

    # Display best odds
    st.subheader("💰 Best Available Odds")
    st.write(f"**Home Win**: {best_odds['home']:.2f}")
    st.write(f"**Draw**: {best_odds['draw']:.2f}")
    st.write(f"**Away Win**: {best_odds['away']:.2f}")

if __name__ == "__main__":
    main()
