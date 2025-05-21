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
            params={"status": "FINISHED", "limit": 10}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Stats Error for {team_name}: {str(e)}")
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
        return (
            joblib.load("model.pkl"),
            joblib.load("scaler.pkl")
        )
    except FileNotFoundError:
        st.error("ML artifacts missing! Please train model first")
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

# ================== UI HELPER FUNCTIONS ================== #
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
    last_10 = matches[-10:]
    for match in last_10:
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            is_winner = team_goals > match["score"]["fullTime"]["away"]
        else:
            team_goals = match["score"]["fullTime"]["away"]
            is_winner = team_goals > match["score"]["fullTime"]["home"]
        goals.append(team_goals)
        wins += 1 if is_winner else 0
    return {
        "avg_goals": np.mean(goals) if goals else 0,
        "win_rate": wins/len(last_10) if matches else 0
    }

# ============== НОВИ ФУНКЦИИ ЗА ФИЛТРИ, СОРТИРАНЕ И ИСТОРИЯ ==============

def filter_and_sort_matches(matches, teams_filter, value_threshold):
    enriched = []
    for m in matches:
        home = m["home_team"]
        away = m["away_team"]
        # Филтър по отбори
        if teams_filter and not (home in teams_filter or away in teams_filter):
            continue
        home_stats = get_team_stats_data(get_team_stats(home), is_home=True)
        away_stats = get_team_stats_data(get_team_stats(away), is_home=False)
        prob = calculate_poisson_probabilities(home_stats["avg_goals"], away_stats["avg_goals"])
        try:
            best_odds = {
                "home": max(o["price"] for b in m["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == home),
                "draw": max(o["price"] for b in m["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
                "away": max(o["price"] for b in m["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == away)
            }
        except:
            best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}
        values = calculate_value_bets(prob, best_odds)
        max_value = max(values.values()) * 100
        if max_value >= value_threshold:
            enriched.append((f"{home} vs {away}", m, prob, best_odds, values, max_value))
    # Сортиране по най-висок value
    enriched.sort(key=lambda x: -x[5])
    return enriched

def save_history(match, probs, odds, values, chosen_outcome):
    row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "match": f"{match['home_team']} vs {match['away_team']}",
        "home_prob": probs[0],
        "draw_prob": probs[1],
        "away_prob": probs[2],
        "home_odds": odds["home"],
        "draw_odds": odds["draw"],
        "away_odds": odds["away"],
        "value_home": values["home"],
        "value_draw": values["draw"],
        "value_away": values["away"],
        "chosen_outcome": chosen_outcome
    }
    if not os.path.exists("data"):
        os.makedirs("data")
    df = pd.DataFrame([row])
    file_path = "data/history.csv"
    if os.path.exists(file_path):
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        df.to_csv(file_path, index=False)

def plot_probabilities(title, labels, probs):
    fig, ax = plt.subplots()
    colors = ["#4CAF50", "#FFC107", "#2196F3"]
    ax.bar(labels, [p * 100 for p in probs], color=colors)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Вероятност (%)")
    ax.set_title(title)
    st.pyplot(fig)

def display_history():
    file_path = "data/history.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        st.dataframe(df.sort_values(by="date", ascending=False), use_container_width=True)
    else:
        st.info("Няма записани прогнози още.")

# ================== MAIN INTERFACE ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    # Sidebar филтри
    value_threshold = st.sidebar.slider("Минимална стойност на залог (%)", 0.0, 20.0, 5.0)
    teams_filter = st.sidebar.multiselect("Филтрирай по отбори", list(TEAM_ID_MAPPING.keys()))

    with st.spinner("Зареждане на живи коефициенти..."):
        matches = get_live_odds()

    if not matches:
        st.warning("Няма налични мачове")
        return

    # Филтриране и сортиране
    filtered_matches = filter_and_sort_matches(matches, teams_filter, value_threshold)
    if not filtered_matches:
        st.warning("Няма мачове, които отговарят на филтрите")
        return

    match_names = [m[0] for m in filtered_matches]
    selected_match_name = st.selectbox("Изберете мач:", match_names)
    selected = next(m for m in filtered_matches if m[0] == selected_match_name)
    match, prob, best_odds, values = selected[1], selected[2], selected[3], selected[4]

    # Статистика за отборите
    home_stats = get_team_stats_data(get_team_stats(match["home_team"]), is_home=True)
    away_stats = get_team_stats_data(get_team_stats(match["away_team"]), is_home=False)

    # Таби
    tab1, tab2, tab3, tab4 = st.tabs(["Анализ на мача", "История на отборите", "AI Прогнози", "История на залозите"])

    with tab1:
        cols = st.columns(3)
        outcomes = [
            ("🏠 Победа домакин", prob[0], values["home"], best_odds["home"]),
            ("⚖ Равен", prob[1], values
