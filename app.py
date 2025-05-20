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
        st.error(f"Stats Error for {team_name}: {str(e)}")
        return []

# ================== ANALYTICS FUNCTIONS ==================

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

def calculate_value_bets(probabilities, odds):
    return {
        'home': (probabilities[0] * odds['home']) - 1,
        'draw': (probabilities[1] * odds['draw']) - 1,
        'away': (probabilities[2] * odds['away']) - 1
    }

# ================== ML FUNCTIONS ==================

def load_ml_artifacts():
    try:
        return (
            joblib.load("model.pkl"),
            joblib.load("scaler.pkl")
        )
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

def get_team_stats_data(matches, is_home=True):
    if not matches:
        return {
            "avg_goals": 1.2 if is_home else 0.9,
            "win_rate": 0.5 if is_home else 0.3
        }

    goals = []
    wins = 0

    for match in matches[-10:]:
        score = match.get("score", {}).get("fullTime", {})
        if score and score.get("home") is not None and score.get("away") is not None:
            is_home_match = match["homeTeam"]["name"] == match["homeTeam"]["name"]
            team_goals = score["home"] if is_home_match else score["away"]
            opp_goals = score["away"] if is_home_match else score["home"]
            goals.append(team_goals)
            if team_goals > opp_goals:
                wins += 1

    avg_goals = np.mean(goals) if goals else 0
    win_rate = wins / len(goals) if goals else 0

    return {
        "avg_goals": avg_goals,
        "win_rate": win_rate
    }

# ================== MAIN INTERFACE ==================

def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    with st.spinner("Loading live odds..."):
        matches = get_live_odds()

    if not matches:
        st.warning("No matches available. Check API key or try later.")
        return

    try:
        match_options = [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
        selected_match = st.selectbox("Select Match:", match_options)
        match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    except StopIteration:
        st.error("Selected match not found.")
        return

    with st.spinner("Analyzing teams..."):
        home_stats = get_team_stats_data(get_team_stats(match["home_team"]) or [], is_home=True)
        away_stats = get_team_stats_data(get_team_stats(match["away_team"]) or [], is_home=False)

    home_odds, draw_odds, away_odds = [], [], []
    for bookmaker in match.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") == "h2h":
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price", 1.0)
                    if name == match["home_team"]:
                        home_odds.append(price)
                    elif name == "Draw":
                        draw_odds.append(price)
                    elif name == match["away_team"]:
                        away_odds.append(price)
    
    best_odds = {
        "home": max(home_odds) if home_odds else 1.0,
        "draw": max(draw_odds) if draw_odds else 1.0,
        "away": max(away_odds) if away_odds else 1.0
    }

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], away_stats["avg_goals"]
    )

    value_bets = calculate_value_bets((prob_home, prob_draw, prob_away), best_odds)

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
            st.subheader(f"Last 10 Matches - {match['home_team']}")
            home_team_name = match['home_team']
            home_matches = get_team_stats(home_team_name) or []
            home_matches = home_matches[-10:]
            
            if home_matches:
                for m in reversed(home_matches):
                    if m:
                        score = m.get("score", {}).get("fullTime", {})
                        if score and 'home' in score and 'away' in score:
                            is_home = m["homeTeam"]["name"] == home_team_name
                            team_goals = score['home'] if is_home else score['away']
                            opp_goals = score['away'] if is_home else score['home']
                            result = f"{team_goals}-{opp_goals}"
                            vs_team = m["awayTeam"]["name"] if is_home else m["homeTeam"]["name"]
                            st.caption(f"{format_date(m['utcDate'])} vs {vs_team} | {result}")
                        else:
                            st.caption(f"{format_date(m['utcDate'])} | Score not available")
            else:
                st.write("No recent matches found")

        with col2:
            st.subheader(f"Last 10 Matches - {match['away_team']}")
            away_team_name = match['away_team']
            away_matches = get_team_stats(away_team_name) or []
            away_matches = away_matches[-10:]
            
            if away_matches:
                for m in reversed(away_matches):
                    if m:
                        score = m.get("score", {}).get("fullTime", {})
                        if score and 'home' in score and 'away' in score:
                            is_home = m["homeTeam"]["name"] == away_team_name
                            team_goals = score['home'] if is_home else score['away']
                            opp_goals = score['away'] if is_home else score['home']
                            result = f"{team_goals}-{opp_goals}"
                            vs_team = m["awayTeam"]["name"] if is_home else m["homeTeam"]["name"]
                            st.caption(f"{format_date(m['utcDate'])} vs {vs_team} | {result}")
                        else:
                            st.caption(f"{format_date(m['utcDate'])} | Score not available")
            else:
                st.write("No recent matches found")

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
                        st.markdown(f"<h2>{prob*100:.1f}%</h2>", unsafe_allow_html=True)

                st.progress(max(prediction))

if __name__ == "__main__":
    main()
