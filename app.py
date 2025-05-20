import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime

# ================== CONFIGURATION ==================
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
SPORT = "soccer"

# Подобрен примерен TEAM_ID_MAPPING с повече отбори
TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Manchester United": 66,
    "Chelsea": 61,
    "Liverpool": 64,
    "Manchester City": 65,
    "Tottenham": 73,
    "Newcastle United": 67,
    "Aston Villa": 58,
    "Brighton": 397,
    "West Ham": 563
}

# ================== API FUNCTIONS ==================
@st.cache_data(ttl=3600)
def get_live_odds():
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "date": today
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
        st.warning(f"⚠ Отборът '{team_name}' липсва в TEAM_ID_MAPPING.")
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
        st.error(f"Грешка при взимане на статистика за {team_name}: {e}")
        return None

# ================== ANALYTICS ==================
def calculate_poisson_probabilities(home_avg, away_avg):
    max_goals = 10
    home_win = draw = away_win = 0
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
        'home': probabilities[0] - 1/odds['home'],
        'draw': probabilities[1] - 1/odds['draw'],
        'away': probabilities[2] - 1/odds['away']
    }

# ================== ML ==================
def load_ml_artifacts():
    try:
        return (
            joblib.load("model.pkl"),
            joblib.load("scaler.pkl")
        )
    except FileNotFoundError:
        st.error("ML artifacts missing! Please train the model first.")
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

# ================== HELPERS ==================
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
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            is_winner = team_goals > match["score"]["fullTime"]["away"]
        else:
            team_goals = match["score"]["fullTime"]["away"]
            is_winner = team_goals > match["score"]["fullTime"]["home"]
        goals.append(team_goals)
        wins += 1 if is_winner else 0
    return {
        "avg_goals": np.mean(goals),
        "win_rate": wins / len(matches)
    }

# ================== MAIN ==================
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    matches = get_live_odds()
    if not matches:
        st.warning("❗ Няма налични мачове за днес.")
        return

    match_names = []
    for m in matches:
        try:
            home = m["bookmakers"][0]["markets"][0]["outcomes"][0]["name"]
            away = m["bookmakers"][0]["markets"][0]["outcomes"][1]["name"]
            match_names.append(f"{home} vs {away}")
        except:
            continue

    selected_match = st.selectbox("Избери мач:", match_names, index=0)

    match = None
    for m in matches:
        try:
            if selected_match == f"{m['bookmakers'][0]['markets'][0]['outcomes'][0]['name']} vs {m['bookmakers'][0]['markets'][0]['outcomes'][1]['name']}":
                match = m
                break
        except:
            continue

    if not match:
        st.error("⚠ Проблем при избора на мач.")
        return

    home_team = match["bookmakers"][0]["markets"][0]["outcomes"][0]["name"]
    away_team = match["bookmakers"][0]["markets"][0]["outcomes"][1]["name"]

    if home_team not in TEAM_ID_MAPPING or away_team not in TEAM_ID_MAPPING:
        st.error(f"Един отбор не е в TEAM_ID_MAPPING: {home_team}, {away_team}")
        st.info("Моля, добави ги ръчно в TEAM_ID_MAPPING в кода.")
        return

    home_raw_stats = get_team_stats(home_team)
    away_raw_stats = get_team_stats(away_team)

    if home_raw_stats is None or away_raw_stats is None:
        st.error("Няма налични статистики за един от отборите.")
        return

    home_stats = get_team_stats_data(home_raw_stats, is_home=True)
    away_stats = get_team_stats_data(away_raw_stats, is_home=False)

    try:
        best_odds = {
            "home": match["bookmakers"][0]["markets"][0]["outcomes"][0]["price"],
            "away": match["bookmakers"][0]["markets"][0]["outcomes"][1]["price"],
            "draw": next(o["price"] for o in match["bookmakers"][0]["markets"][0]["outcomes"] if o["name"].lower() == "draw")
        }
    except:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}

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
            st.subheader(f"Last 10 Matches - {home_team}")
            for m in reversed(home_raw_stats[-10:]):
                score = m["score"]["fullTime"]
                st.caption(f"{format_date(m['utcDate'])} | {score['home']}-{score['away']}")
        with col2:
            st.subheader(f"Last 10 Matches - {away_team}")
            for m in reversed(away_raw_stats[-10:]):
                score = m["score"]["fullTime"]
                st.caption(f"{format_date(m['utcDate'])} | {score['away']}-{score['home']}")

    with tab3:
        if st.button("Генерирай AI прогноза"):
            with st.spinner("Анализ..."):
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
    
