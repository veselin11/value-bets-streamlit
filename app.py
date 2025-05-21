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

# ================ CONFIGURATION ================= #
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

HISTORY_FILE = "bet_history.csv"

# ================ API FUNCTIONS ================= #
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

# ================ ANALYTICS FUNCTIONS =============== #
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
        'home': probabilities[0] - 1/odds['home'],
        'draw': probabilities[1] - 1/odds['draw'],
        'away': probabilities[2] - 1/odds['away']
    }

# ================ ML FUNCTIONS ===================== #
def load_ml_artifacts():
    try:
        return joblib.load("model.pkl"), joblib.load("scaler.pkl")
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

# ================ UI HELPERS ======================= #
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, is_home=True):
    if not matches:
        return {"avg_goals": 1.2 if is_home else 0.9, "win_rate": 0.5 if is_home else 0.3}
    goals = []
    wins = 0
    for match in matches[-10:]:
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            opp_goals = match["score"]["fullTime"]["away"]
        else:
            team_goals = match["score"]["fullTime"]["away"]
            opp_goals = match["score"]["fullTime"]["home"]
        goals.append(team_goals)
        wins += 1 if team_goals > opp_goals else 0
    return {"avg_goals": np.mean(goals) if goals else 0, "win_rate": wins/len(matches[-10:])}

def plot_probabilities(title, labels, probabilities):
    fig, ax = plt.subplots()
    ax.bar(labels, probabilities, color=["#4CAF50", "#FFC107", "#2196F3"])
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_ylabel("Вероятност")
    st.pyplot(fig)

# ================ HISTORY MANAGEMENT =============== #
def save_history(match, probabilities, odds, values, chosen):
    row = {
        "datetime": datetime.now().isoformat(),
        "match": f"{match['home_team']} vs {match['away_team']}",
        "prob_home": probabilities[0],
        "prob_draw": probabilities[1],
        "prob_away": probabilities[2],
        "odds_home": odds["home"],
        "odds_draw": odds["draw"],
        "odds_away": odds["away"],
        "value_home": values["home"],
        "value_draw": values["draw"],
        "value_away": values["away"],
        "chosen_bet": chosen
    }
    df = pd.DataFrame([row])
    if os.path.exists(HISTORY_FILE):
        df.to_csv(HISTORY_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(HISTORY_FILE, index=False)

def display_history():
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        filter_team = st.text_input("Филтрирай по отбор (частично име):")
        if filter_team:
            df = df[df['match'].str.contains(filter_team, case=False)]
        st.dataframe(df)
    else:
        st.info("Все още няма записана история.")

def display_team_history(team_name):
    matches = get_team_stats(team_name)
    if matches:
        for m in reversed(matches):
            home = m["home_team"]["name"]
            away = m["away_team"]["name"]
            score = f"{m['score']['fullTime']['home']} : {m['score']['fullTime']['away']}"
            st.caption(f"{format_date(m['utcDate'])} | {home} {score} {away}")
    else:
        st.write("Няма намерени мачове за отбора.")

# ================ MAIN APP ========================= #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    with st.spinner("Зареждане на live коефициенти..."):
        matches = get_live_odds()

    if not matches:
        st.warning("Няма налични мачове в момента.")
        return

    match_options = [f"{m['home_team']} vs {m['away_team']}" for m in matches]
    selected_match = st.selectbox("Изберете мач:", match_options)

    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)

    with st.spinner("Анализ на отборите..."):
        home_matches = get_team_stats(match["home_team"])
        away_matches = get_team_stats(match["away_team"])

        home_stats = get_team_stats_data(home_matches, is_home=True)
        away_stats = get_team_stats_data(away_matches, is_home=False)

    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
            "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
        }
    except Exception:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}

    prob = calculate_poisson_probabilities(home_stats["avg_goals"], away_stats["avg_goals"])
    values = calculate_value_bets(prob, best_odds)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Анализ на мача",
        "История на отборите",
        "AI Прогнози",
        "История на залозите",
        "История на избран отбор"
    ])

    with tab1:
        cols = st.columns(3)
        outcomes = [
            (match["home_team"], prob[0], values["home"], best_odds["home"]),
            ("Равен", prob[1], values["draw"], best_odds["draw"]),
            (match["away_team"], prob[2], values["away"], best_odds["away"])
        ]
        for col, (label, probability, value, odds) in zip(cols, outcomes):
            col.metric(label, f"{probability*100:.1f}%", delta=f"Value: {value*100:.2f}%")
            col.write(f"Коефициент: {odds:.2f}")

        plot_probabilities(
            f"Вероятности за {match['home_team']} vs {match['away_team']}",
            [match["home_team"], "Равен", match["away_team"]],
            prob
        )

        chosen = st.radio("Изберете залог за запазване:", [o[0] for o in outcomes])
        if st.button("Запази прогноза"):
            save_history(match, prob, best_odds, values, chosen)
            st.success("Прогнозата е
