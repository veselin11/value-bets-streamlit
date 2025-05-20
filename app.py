import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
import joblib
from datetime import datetime
import traceback

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
        st.error(f"Odds API Error: {e}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        st.warning(f"Unknown team: {team_name}")
        return []
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 10}
        )
        response.raise_for_status()
        data = response.json()
        matches = data.get("matches", [])
        if matches is None:
            matches = []
        return matches
    except Exception as e:
        st.error(f"Stats Error for {team_name}: {e}")
        return []

# ================== ANALYTICS FUNCTIONS ================== #
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
    try:
        return {
            'home': probabilities[0] - 1/odds['home'],
            'draw': probabilities[1] - 1/odds['draw'],
            'away': probabilities[2] - 1/odds['away']
        }
    except Exception:
        return {'home': 0, 'draw': 0, 'away': 0}

# ================== ML FUNCTIONS ================== #
def load_ml_artifacts():
    try:
        model = joblib.load("model.pkl")
        scaler = joblib.load("scaler.pkl")
        return model, scaler
    except Exception as e:
        st.error(f"ML artifacts loading error: {e}")
        return None, None

def predict_with_ai(home_stats, away_stats):
    model, scaler = load_ml_artifacts()
    if not model or not scaler:
        return None
    features = np.array([
        home_stats.get("avg_goals", 0),
        away_stats.get("avg_goals", 0),
        home_stats.get("win_rate", 0),
        away_stats.get("win_rate", 0)
    ]).reshape(1, -1)
    try:
        scaled = scaler.transform(features)
        return model.predict_proba(scaled)[0]
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

# ================== UI HELPERS ================== #
def format_date(iso_date):
    try:
        return datetime.fromisoformat(iso_date.replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        return iso_date

def get_team_stats_data(matches, is_home=True):
    if not matches:
        return {"avg_goals": 1.2 if is_home else 0.9, "win_rate": 0.5 if is_home else 0.3}

    goals = []
    wins = 0
    count = 0

    for match in matches[-10:]:
        score = match.get("score", {}).get("fullTime")
        if not score or score.get("home") is None or score.get("away") is None:
            continue
        count += 1
        if is_home:
            team_goals = score["home"]
            opp_goals = score["away"]
        else:
            team_goals = score["away"]
            opp_goals = score["home"]
        goals.append(team_goals)
        if team_goals > opp_goals:
            wins += 1

    avg_goals = np.mean(goals) if goals else (1.2 if is_home else 0.9)
    win_rate = wins/count if count > 0 else (0.5 if is_home else 0.3)
    return {"avg_goals": avg_goals, "win_rate": win_rate}

# ================== MAIN ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    try:
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
            home_matches_raw = get_team_stats(match["home_team"])
            away_matches_raw = get_team_stats(match["away_team"])

            home_stats = get_team_stats_data(home_matches_raw, is_home=True)
            away_stats = get_team_stats_data(away_matches_raw, is_home=False)

        # Odds processing
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}
        try:
            if "bookmakers" in match and match["bookmakers"]:
                best_odds = {
                    "home": max(
                        o["price"]
                        for b in match["bookmakers"]
                        for o in b["markets"][0]["outcomes"]
                        if o["name"] == match["home_team"]
                    ),
                    "draw": max(
                        o["price"]
                        for b in match["bookmakers"]
                        for o in b["markets"][0]["outcomes"]
                        if o["name"] == "Draw"
                    ),
                    "away": max(
                        o["price"]
                        for b in match["bookmakers"]
                        for o in b["markets"][0]["outcomes"]
                        if o["name"] == match["away_team"]
                    ),
                }
        except Exception:
            pass  # fallback odds kept

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
                    st.markdown(f"**Value:** <span style='color:{value_color}'>{(value*100):.1f}%</span>", unsafe_allow_html=True)

        with tab2:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader(f"Last 10 Matches - {match['home_team']}")
                home_matches = home_matches_raw[-10:] if home_matches_raw else []
                if home_matches:
                    for m in reversed(home_matches):
                        score = m.get("score", {}).get("fullTime")
                        if score and score.get("home
