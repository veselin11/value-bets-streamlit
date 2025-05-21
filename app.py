# Smart Bet Advisor with Multi-League Support
import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

LEAGUES = {
    "Premier League": {"odds_sport": "soccer_epl", "football_data_code": "PL"},
    "La Liga": {"odds_sport": "soccer_spain_la_liga", "football_data_code": "PD"},
    "Bundesliga": {"odds_sport": "soccer_germany_bundesliga", "football_data_code": "BL1"},
    "Serie A": {"odds_sport": "soccer_italy_serie_a", "football_data_code": "SA"},
    "Ligue 1": {"odds_sport": "soccer_france_ligue_one", "football_data_code": "FL1"}
}

TEAM_ID_MAPPING = {
    # Add teams with their Football-Data.org team IDs
    "Arsenal": 57, "Barcelona": 81, "Bayern Munich": 5, "Juventus": 109, "PSG": 524,
    # Add more teams as needed
}

# ================== API FUNCTIONS ================== #
@st.cache_data(ttl=3600)
def get_live_odds(odds_sport_code):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{odds_sport_code}/odds",
            params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name, competition_code):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id or not competition_code:
        return []
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 10, "competitions": competition_code}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Stats Error: {str(e)}")
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
    return {
        'home': probabilities[0] - 1/odds['home'],
        'draw': probabilities[1] - 1/odds['draw'],
        'away': probabilities[2] - 1/odds['away']
    }

# ================== ML FUNCTIONS ================== #
def load_ml_artifacts():
    try:
        return joblib.load("model.pkl"), joblib.load("scaler.pkl")
    except FileNotFoundError:
        st.error("ML artifacts missing! Train model first.")
        return None, None

def predict_with_ai(home_stats, away_stats):
    model, scaler = load_ml_artifacts()
    if not model: return None
    features = np.array([
        home_stats["avg_goals"], away_stats["avg_goals"],
        home_stats["win_rate"], away_stats["win_rate"]
    ]).reshape(1, -1)
    return model.predict_proba(scaler.transform(features))[0]

# ================== UTILS ================== #
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, is_home=True):
    if not matches:
        return {"avg_goals": 1.0, "win_rate": 0.4}
    goals, wins = [], 0
    for match in matches[-10:]:
        if is_home:
            goals_scored = match["score"]["fullTime"]["home"]
            won = goals_scored > match["score"]["fullTime"]["away"]
        else:
            goals_scored = match["score"]["fullTime"]["away"]
            won = goals_scored > match["score"]["fullTime"]["home"]
        goals.append(goals_scored)
        wins += 1 if won else 0
    return {"avg_goals": np.mean(goals), "win_rate": wins/len(matches)}

# ================== MAIN INTERFACE ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    league_name = st.selectbox("Избери първенство:", list(LEAGUES.keys()))
    selected_league = LEAGUES[league_name]
    odds_sport_code = selected_league["odds_sport"]
    football_data_code = selected_league["football_data_code"]

    with st.spinner("Зареждане на коефициенти..."):
        matches = get_live_odds(odds_sport_code)

    if not matches:
        st.warning("Няма налични мачове")
        return

    selected_match = st.selectbox(
        "Избери мач:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)

    with st.spinner("Анализ на отборите..."):
        home_stats = get_team_stats_data(get_team_stats(match["home_team"], football_data_code), is_home=True)
        away_stats = get_team_stats_data(get_team_stats(match["away_team"], football_data_code), is_home=False)

    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
            "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
        }
    except:
        best_odds = {"home": 1.5, "draw": 3.8, "away": 5.0}

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
        for col, (label, prob, value, odds) in zip(cols, outcomes):
            with col:
                st.subheader(label)
                st.metric("Probability", f"{prob*100:.1f}%")
                st.metric("Odds", f"{odds:.2f}")
                color = "green" if value > 0 else "red"
                st.markdown(f"**Value:** <span style='color:{color}'>{value*100:.1f}%</span>", unsafe_allow_html=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"{match['home_team']} - Last 10 Matches")
            for m in reversed(get_team_stats(match["home_team"], football_data_code)[-10:]):
                result = f"{m['score']['fullTime']['home']}-{m['score']['fullTime']['away']}"
                st.caption(f"{format_date(m['utcDate'])} | {result}")
        with col2:
            st.subheader(f"{match['away_team']} - Last 10 Matches")
            for m in reversed(get_team_stats(match["away_team"], football_data_code)[-10:]):
                result = f"{m['score']['fullTime']['away']}-{m['score']['fullTime']['home']}"
                st.caption(f"{format_date(m['utcDate'])} | {result}")

    with tab3:
        if st.button("Generate AI Prediction"):
            prediction = predict_with_ai(home_stats, away_stats)
            if prediction is not None:
                st.subheader("🤖 AI Prediction")
                labels = ["Home Win", "Draw", "Away Win"]
                colors = ["#4CAF50", "#FFC107", "#2196F3"]
                cols = st.columns(3)
                for col, label, prob, color in zip(cols, labels, prediction, colors):
                    with col:
                        st.markdown(f"<h3 style='color:{color}'>{label}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<h2>{prob*100:.1f}%</h2>", unsafe_allow_html=True)
                st.progress(max(prediction))

if __name__ == "__main__":
    main()
    
