import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime
import os

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

LEAGUE_OPTIONS = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
    "Serie A": "soccer_italy_serie_a",
    "Ligue 1": "soccer_france_ligue_one"
}

TEAM_ID_MAPPING = {
    "Arsenal": 57, "Aston Villa": 58, "Brentford": 402, "Brighton & Hove Albion": 397,
    "Burnley": 328, "Chelsea": 61, "Crystal Palace": 354, "Everton": 62,
    "Fulham": 63, "Liverpool": 64, "Luton Town": 389, "Manchester City": 65,
    "Manchester United": 66, "Newcastle United": 67, "Nottingham Forest": 351,
    "Sheffield United": 356, "Tottenham Hotspur": 73, "West Ham United": 563,
    "Wolverhampton Wanderers": 76, "AFC Bournemouth": 1044
    # Add more if needed
}

BET_HISTORY_FILE = "bet_history.csv"

# ================== API FUNCTIONS ================== #
@st.cache_data(ttl=3600)
def get_live_odds(sport_key):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
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

# ================== ANALYTICS FUNCTIONS ================== #
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
    return home_win / total, draw / total, away_win / total

def calculate_value_bets(probabilities, odds):
    return {
        'home': probabilities[0] - 1 / odds['home'],
        'draw': probabilities[1] - 1 / odds['draw'],
        'away': probabilities[2] - 1 / odds['away']
    }

# ================== ML FUNCTIONS ================== #
def load_ml_artifacts():
    try:
        return joblib.load("model.pkl"), joblib.load("scaler.pkl")
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

# ================== UTILITIES ================== #
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, is_home=True):
    if not matches:
        return {"avg_goals": 1.2 if is_home else 0.9, "win_rate": 0.5 if is_home else 0.3}
    goals, wins = [], 0
    for match in matches[-10:]:
        team_goals = match["score"]["fullTime"]["home"] if is_home else match["score"]["fullTime"]["away"]
        opponent_goals = match["score"]["fullTime"]["away"] if is_home else match["score"]["fullTime"]["home"]
        goals.append(team_goals)
        wins += 1 if team_goals > opponent_goals else 0
    return {"avg_goals": np.mean(goals), "win_rate": wins / len(matches[-10:])}

def log_bet(match_name, outcome, odds, value):
    new_entry = pd.DataFrame([{
        "Match": match_name,
        "Outcome": outcome,
        "Odds": odds,
        "Value": value,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    if os.path.exists(BET_HISTORY_FILE):
        df = pd.read_csv(BET_HISTORY_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
    else:
        df = new_entry
    df.to_csv(BET_HISTORY_FILE, index=False)

# ================== MAIN APP ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    league_name = st.selectbox("Избери първенство:", list(LEAGUE_OPTIONS.keys()))
    sport_key = LEAGUE_OPTIONS[league_name]

    matches = get_live_odds(sport_key)
    if not matches:
        st.warning("Няма налични мачове")
        return

    match_options = [
        f"{m['home_team']} vs {m['away_team']} ({m['commence_time'].split('T')[0]})"
        for m in matches
    ]
    selected = st.selectbox("Избери мач:", match_options)
    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" in selected)

    home_stats = get_team_stats_data(get_team_stats(match["home_team"]), is_home=True)
    away_stats = get_team_stats_data(get_team_stats(match["away_team"]), is_home=False)

    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
            "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
        }
    except:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}

    prob = calculate_poisson_probabilities(home_stats["avg_goals"], away_stats["avg_goals"])
    values = calculate_value_bets(prob, best_odds)

    st.subheader("Стойностни залози")
    cols = st.columns(3)
    outcomes = [
        (f"Победа {match['home_team']}", prob[0], values['home'], best_odds['home']),
        ("Равенство", prob[1], values['draw'], best_odds['draw']),
        (f"Победа {match['away_team']}", prob[2], values['away'], best_odds['away'])
    ]
    for col, (label, p, v, odd) in zip(cols, outcomes):
        with col:
            st.metric(label, f"{p*100:.1f}%")
            st.metric("Коефициент", f"{odd:.2f}")
            st.markdown(f"**Стойност:** {'+' if v > 0 else ''}{v*100:.1f}%")
            if v > 0 and st.button(f"Заложи: {label}", key=label):
                log_bet(f"{match['home_team']} vs {match['away_team']}", label, odd, f"{v*100:.1f}%")
                st.success("Залогът е добавен в историята!")

    st.subheader("Последни 10 мача")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"{match['home_team']}")
        for m in get_team_stats(match["home_team"])[-10:]:
            opp = m['awayTeam']['name']
            goals = m['score']['fullTime']['home']
            opp_goals = m['score']['fullTime']['away']
            result = "Победа" if goals > opp_goals else ("Равен" if goals == opp_goals else "Загуба")
            st.caption(f"{format_date(m['utcDate'])} срещу {opp} | {goals}-{opp_goals} | {result}")
    with col2:
        st.write(f"{match['away_team']}")
        for m in get_team_stats(match["away_team"])[-10:]:
            opp = m['homeTeam']['name']
            goals = m['score']['fullTime']['away']
            opp_goals = m['score']['fullTime']['home']
            result = "Победа" if goals > opp_goals else ("Равен" if goals == opp_goals else "Загуба")
            st.caption(f"{format_date(m['utcDate'])} срещу {opp} | {goals}-{opp_goals} | {result}")

    st.subheader("История на залозите")
    if os.path.exists(BET_HISTORY_FILE):
        history_df = pd.read_csv(BET_HISTORY_FILE)
        st.dataframe(history_df.sort_values("Timestamp", ascending=False))
    else:
        st.info("Все още няма запазени залози.")

if __name__ == "__main__":
    main()
    
