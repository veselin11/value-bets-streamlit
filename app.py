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

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
SPORT = "soccer_epl"

TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Aston Villa": 58,
    "Brentford": 402,
    "Brighton": 397,  # Updated if necessary
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
    "Wolves": 76,  # Updated if necessary
    "Bournemouth": 1044  # Corrected name
}

# ================== API FUNCTIONS ================== #
@st.cache_data(ttl=3600)
def get_live_odds():
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
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return None
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED"}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Stats Error for {team_name}: {str(e)}")
        return []

# ================== ANALYTICS ================== #
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
    return home_win / total, draw / total, away_win / total

def calculate_value_bets(probabilities, odds):
    return {
        'home': (probabilities[0] * odds['home']) - 1,
        'draw': (probabilities[1] * odds['draw']) - 1,
        'away': (probabilities[2] * odds['away']) - 1
    }

# ================== ML FUNCTIONS ================== #
def load_ml_artifacts():
    try:
        return (
            joblib.load("model.pkl"),
            joblib.load("scaler.pkl")
        )
    except FileNotFoundError:
        st.error("ML artifacts missing! Please train model first")
        return None, None

def predict_with_ai(home_stats, away_stats):
    model, scaler = load_ml_artifacts()
    if not model:
        return None
    features = np.array([
        home_stats["avg_goals"],
        away_stats["avg_goals"],
        home_stats["win_rate"],
        away_stats["win_rate"]
    ]).reshape(1, -1)
    return model.predict_proba(scaler.transform(features))[0]

# ================== UI HELPERS ================== #
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, team_name, is_home=True):
    if not matches:
        return {
            "avg_goals": 1.2 if is_home else 0.9,
            "win_rate": 0.5 if is_home else 0.3
        }
    relevant_matches = []
    for match in matches:
        if is_home:
            if match['homeTeam']['name'] == team_name:
                relevant_matches.append(match)
        else:
            if match['awayTeam']['name'] == team_name:
                relevant_matches.append(match)
    recent_matches = relevant_matches[-10:]  # Take last 10 relevant matches
    goals = []
    wins = 0
    for match in recent_matches:
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            opponent_goals = match["score"]["fullTime"]["away"]
        else:
            team_goals = match["score"]["fullTime"]["away"]
            opponent_goals = match["score"]["fullTime"]["home"]
        goals.append(team_goals)
        if team_goals > opponent_goals:
            wins += 1
    avg_goals = np.mean(goals) if goals else 0
    win_rate = wins / len(recent_matches) if recent_matches else 0
    return {"avg_goals": avg_goals, "win_rate": win_rate}

# ================== MAIN INTERFACE ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    with st.spinner("Loading live odds..."):
        matches = get_live_odds()

    if not matches:
        st.warning("No matches available")
        return

    selected_match = st.selectbox(
        "Select Match:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches],
        index=0
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)

    with st.spinner("Analyzing teams..."):
        home_team = match["home_team"]
        away_team = match["away_team"]
        home_matches = get_team_stats(home_team)
        away_matches = get_team_stats(away_team)
        home_stats = get_team_stats_data(home_matches, home_team, is_home=True)
        away_stats = get_team_stats_data(away_matches, away_team, is_home=False)

    best_odds = {"home": 1.0, "draw": 1.0, "away": 1.0}
    for bookmaker in match.get("bookmakers", []):
        for outcome in bookmaker.get("markets", [{}])[0].get("outcomes", []):
            name = outcome.get("name")
            price = outcome.get("price", 1.0)
            if name == home_team and price > best_odds["home"]:
                best_odds["home"] = price
            elif name == "Draw" and price > best_odds["draw"]:
                best_odds["draw"] = price
            elif name == away_team and price > best_odds["away"]:
                best_odds["away"] = price

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"],
        away_stats["avg_goals"]
    )

    value_bets = calculate_value_bets(
        (prob_home, prob_draw, prob_away),
        best_odds
    )

    tab1, tab2, tab3 = st.tabs(["Match Analysis", "Team History", "AI Predictions"])

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
            st.subheader(f"Last 10 Home Matches - {home_team}")
            home_recent = [m for m in home_matches if m['homeTeam']['name'] == home_team][-10:]
            if home_recent:
                for m in reversed(home_recent):
                    result = f"{m['score']['fullTime']['home']}-{m['score']['fullTime']['away']}"
                    st.caption(f"{format_date(m['utcDate'])} | {result}")
            else:
                st.write("No recent home matches found")
        with col2:
            st.subheader(f"Last 10 Away Matches - {away_team}")
            away_recent = [m for m in away_matches if m['awayTeam']['name'] == away_team][-10:]
            if away_recent:
                for m in reversed(away_recent):
                    result = f"{m['score']['fullTime']['away']}-{m['score']['fullTime']['home']}"
                    st.caption(f"{format_date(m['utcDate'])} | {result}")
            else:
                st.write("No recent away matches found")

    with tab3:
        if st.button("Generate AI Prediction"):
            with st.spinner("Analyzing..."):
                prediction = predict_with_ai(home_stats, away_stats)
            if prediction is not None:
                st.subheader("🤖 AI Prediction Results")
                cols = st.columns(3)
                labels = ["Home Win", "Draw", "Away Win"]
                colors = ["#4CAF50", "#FFC107", "#2196F3"]
                for col, label, prob, color in zip(cols, labels, prediction, colors):
                    with col:
                        st.markdown(f"<h3 style='color:{color}'>{label}</h3>", unsafe_allow_html=True)
                        st.metric("Probability", f"{prob*100:.1f}%")

if __name__ == "__main__":
    main()
