import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

# ================== API КЛЮЧОВЕ ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

# ================== КЕШВАНЕ НА API ЗА ПЪРВЕНСТВА ================== #
@st.cache_data(ttl=86400)
def get_soccer_leagues():
    url = "https://api.the-odds-api.com/v4/sports"
    response = requests.get(url, params={"apiKey": ODDS_API_KEY})
    response.raise_for_status()
    data = response.json()
    soccer_leagues = [s for s in data if s["group"].lower().startswith("soccer") and s["active"]]
    return soccer_leagues

@st.cache_data(ttl=3600)
def get_odds_for_league(key):
    url = f"https://api.the-odds-api.com/v4/sports/{key}/odds"
    response = requests.get(url, params={
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    })
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=3600)
def get_team_stats(team_id):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches"
    response = requests.get(url, headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY}, params={"status": "FINISHED", "limit": 20})
    response.raise_for_status()
    return response.json()["matches"]

# ================== ПОМОЩНИ ФУНКЦИИ ================== #
def calculate_poisson_probabilities(home_avg, away_avg):
    home_win, draw, away_win = 0, 0, 0
    for i in range(0, 6):
        for j in range(0, 6):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p
    return home_win, draw, away_win

def calculate_value_bets(probabilities, odds):
    value = {}
    for outcome in ['home', 'draw', 'away']:
        implied_prob = 1 / odds[outcome]
        value[outcome] = probabilities[outcome] - implied_prob
    return value

def process_team_stats(matches, is_home):
    if not matches:
        return {"avg_goals": 1.0, "win_rate": 0.5}
    goals = []
    wins = 0
    for m in matches[-10:]:
        score = m["score"]["fullTime"]
        if score["home"] is None or score["away"] is None:
            continue
        if is_home:
            goals.append(score["home"])
            if score["home"] > score["away"]:
                wins += 1
        else:
            goals.append(score["away"])
            if score["away"] > score["home"]:
                wins += 1
    total = len(goals)
    win_rate = wins / total if total > 0 else 0
    avg_goals = np.mean(goals) if goals else 1.0
    return {"avg_goals": avg_goals, "win_rate": win_rate}

def predict_with_ai(home_stats, away_stats):
    try:
        model = joblib.load("model.pkl")
        scaler = joblib.load("scaler.pkl")
        features = np.array([
            home_stats["avg_goals"],
            away_stats["avg_goals"],
            home_stats["win_rate"],
            away_stats["win_rate"]
        ]).reshape(1, -1)
        scaled_features = scaler.transform(features)
        prediction = model.predict_proba(scaled_features)
        return prediction[0]
    except:
        return None

# ================== UI ================== #
def main():
    st.set_page_config(page_title="Advanced Bet Analyzer", layout="wide", page_icon="⚽")
    st.title("🔮 Advanced Bet Analyzer")

    leagues = get_soccer_leagues()
    league_names = {league["title"]: league["key"] for league in leagues}
    selected_league_name = st.selectbox("Избери първенство", list(league_names.keys()))
    selected_league_key = league_names[selected_league_name]

    matches = get_odds_for_league(selected_league_key)
    if not matches:
        st.warning("Няма мачове за избраното първенство.")
        return

    selected_match = st.selectbox(
        "Избери мач за анализ:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)

    st.subheader("Зареждане на статистики...")
    home_team = match["home_team"]
    away_team = match["away_team"]
    home_id = None
    away_id = None

    for team in get_team_stats.__wrapped__.__globals__["TEAM_ID_MAPPING"]:
        if team.lower() in home_team.lower():
            home_id = get_team_stats.__wrapped__.__globals__["TEAM_ID_MAPPING"][team]
        if team.lower() in away_team.lower():
            away_id = get_team_stats.__wrapped__.__globals__["TEAM_ID_MAPPING"][team]

    if not home_id or not away_id:
        st.warning("Няма статистика за поне един от отборите.")
        return

    home_stats_raw = get_team_stats(home_id)
    away_stats_raw = get_team_stats(away_id)

    home_stats = process_team_stats(home_stats_raw, is_home=True)
    away_stats = process_team_stats(away_stats_raw, is_home=False)

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], away_stats["avg_goals"]
    )

    best_odds = {
        "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == home_team),
        "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
        "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == away_team)
    }

    value_bets = calculate_value_bets(
        {"home": prob_home, "draw": prob_draw, "away": prob_away},
        best_odds
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏠 Победа домакин", f"{prob_home*100:.1f}%", delta=f"{value_bets['home']*100:.1f}%")
    with col2:
        st.metric("⚖ Равен", f"{prob_draw*100:.1f}%", delta=f"{value_bets['draw']*100:.1f}%")
    with col3:
        st.metric("✈ Победа гост", f"{prob_away*100:.1f}%", delta=f"{value_bets['away']*100:.1f}%")

    if st.button("AI Прогноза"):
        ai = predict_with_ai(home_stats, away_stats)
        if ai is not None:
            st.success("AI Прогноза:")
            st.write(f"- Победа {home_team}: {ai[0]*100:.1f}%")
            st.write(f"- Равен: {ai[1]*100:.1f}%")
            st.write(f"- Победа {away_team}: {ai[2]*100:.1f}%")

if __name__ == "__main__":
    main()
