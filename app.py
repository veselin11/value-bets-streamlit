import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

# ================== КЛЮЧОВЕ ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

# ================== API ДАННИ ================== #
@st.cache_data(ttl=3600)
def get_supported_football_leagues():
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY}
        )
        response.raise_for_status()
        sports = response.json()
        football_sports = [
            s for s in sports
            if s["group"] == "Soccer" and s["active"]
        ]
        return {s["title"]: s["key"] for s in football_sports}
    except Exception as e:
        st.error(f"Грешка при зареждане на първенства: {str(e)}")
        return {}

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
        st.error(f"Грешка при взимане на коефициенти: {str(e)}")
        return []

# ================== ДАННИ ЗА ОТБОРИ ================== #
TEAM_ID_MAPPING = {
    "Manchester City": 65,
    "Liverpool": 64,
    "Arsenal": 57,
    "Everton": 62,
    "Tottenham Hotspur": 73,
    # добави още отбори по желание
}

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return None
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 20}
        )
        response.raise_for_status()
        return response.json()["matches"]
    except Exception as e:
        st.warning(f"Статистика недостъпна за {team_name}")
        return None

# ================== АНАЛИЗ ================== #
def calculate_poisson_probabilities(home_avg, away_avg):
    home_win, draw, away_win = 0, 0, 0
    for i in range(6):
        for j in range(6):
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
        if is_home:
            goals.append(score["home"])
            if score["home"] > score["away"]:
                wins += 1
        else:
            goals.append(score["away"])
            if score["away"] > score["home"]:
                wins += 1
    win_rate = wins / len(goals) if goals else 0
    avg_goals = np.mean(goals) if goals else 1.0
    return {"avg_goals": avg_goals, "win_rate": win_rate}

# ================== AI МОДЕЛ ================== #
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
        scaled = scaler.transform(features)
        return model.predict_proba(scaled)[0]
    except:
        return None

# ================== STREAMLIT ================== #
def main():
    st.set_page_config(page_title="Advanced Bet Analyzer", layout="wide")
    st.title("🔮 Advanced Bet Analyzer")

    leagues = get_supported_football_leagues()
    if not leagues:
        return

    league_name = st.selectbox("Избери първенство", list(leagues.keys()))
    league_key = leagues[league_name]

    matches = get_live_odds(league_key)
    if not matches:
        st.warning("Няма активни мачове.")
        return

    selected_match = st.selectbox(
        "Избери мач за анализ:",
        [f"{m['home_team']} vs {m['away_team']}" for m in matches]
    )
    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)

    home_stats_raw = get_team_stats(match["home_team"])
    away_stats_raw = get_team_stats(match["away_team"])
    home_stats = process_team_stats(home_stats_raw, is_home=True)
    away_stats = process_team_stats(away_stats_raw, is_home=False)

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], away_stats["avg_goals"]
    )

    best_odds = {
        "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
        "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
        "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
    }

    value_bets = calculate_value_bets(
        {"home": prob_home, "draw": prob_draw, "away": prob_away},
        best_odds
    )

    tab1, tab2, tab3 = st.tabs(["Основен анализ", "Разширена статистика", "AI Прогноза"])

    with tab1:
        st.metric("Шанс за победа (Домакин)", f"{prob_home*100:.1f}%")
        st.metric("Шанс за равен", f"{prob_draw*100:.1f}%")
        st.metric("Шанс за победа (Гост)", f"{prob_away*100:.1f}%")

    with tab2:
        st.write("Последни мачове недостъпни за някои отбори, ако не са от EPL.")
        if home_stats_raw:
            st.write(f"Последни мачове за {match['home_team']}")
            for m in home_stats_raw[-5:]:
                score = m["score"]["fullTime"]
                st.write(f"{score['home']} - {score['away']}")

    with tab3:
        if st.button("Генерирай AI прогноза"):
            pred = predict_with_ai(home_stats, away_stats)
            if pred is not None:
                st.success(f"Победа {match['home_team']}: {pred[0]*100:.1f}%")
                st.info(f"Равен: {pred[1]*100:.1f}%")
                st.success(f"Победа {match['away_team']}: {pred[2]*100:.1f}%")
            else:
                st.warning("AI прогнозата не е налична.")

if __name__ == "__main__":
    main()
