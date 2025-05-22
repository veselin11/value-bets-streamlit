import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

# ================== КОНФИГУРАЦИЯ ================== #
LEAGUES = {
    "Англия - Висша лига": "soccer_epl",
    "Испания - Ла Лига": "soccer_spain_la_liga",
    "Италия - Серия А": "soccer_italy_serie_a",
    "Германия - Бундеслига": "soccer_germany_bundesliga",
    "Франция - Лига 1": "soccer_france_ligue_one"
}

FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

TEAM_ID_MAPPING = {
    "Manchester City": 65,
    "AFC Bournemouth": 1044,
    "Liverpool": 64,
    "Everton": 62,
    "Arsenal": 57,
    "Tottenham Hotspur": 73,
    # ... добави още отбори при нужда
}

# ================== API ================== #
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
        st.error(f"Грешка при взимане на статистики за {team_name}: {str(e)}")
        return None

# ================== АНАЛИЗ ================== #
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

# ================== AI ================== #
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
    except Exception as e:
        st.error(f"Грешка при AI прогноза: {str(e)}")
        return None

# ================== Обработка ================== #
def process_team_stats(matches, is_home):
    if not matches:
        return {"avg_goals": 1.0, "win_rate": 0.5, "avg_conceded": 1.0, "btts_rate": 0.5, "over_2_5_rate": 0.5}

    recent = matches[-10:] if len(matches) >= 10 else matches
    goals, conceded = [], []
    wins = btts = over_2_5 = 0

    for m in recent:
        score = m["score"]["fullTime"]
        home, away = score.get("home", 0), score.get("away", 0)
        g, c = (home, away) if is_home else (away, home)
        goals.append(g)
        conceded.append(c)
        if g > c: wins += 1
        if g > 0 and c > 0: btts += 1
        if (g + c) > 2.5: over_2_5 += 1

    count = len(recent)
    return {
        "avg_goals": np.mean(goals),
        "win_rate": wins / count,
        "avg_conceded": np.mean(conceded),
        "btts_rate": btts / count,
        "over_2_5_rate": over_2_5 / count
    }

# ================== UI ================== #
def main():
    st.set_page_config(page_title="Advanced Bet Analyzer", layout="wide")
    st.title("🔮 Advanced Bet Analyzer")

    selected_league = st.selectbox("Избери първенство:", list(LEAGUES.keys()))
    sport_key = LEAGUES[selected_league]

    matches = get_live_odds(sport_key)
    if not matches:
        st.warning("Няма мачове.")
        return

    selected_match = st.selectbox(
        "Избери мач:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)

    home_stats_raw = get_team_stats(match["home_team"])
    away_stats_raw = get_team_stats(match["away_team"])

    home_stats = process_team_stats(home_stats_raw, True)
    away_stats = process_team_stats(away_stats_raw, False)

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], away_stats["avg_goals"])

    best_odds = {
        "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
        "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
        "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
    }

    value_bets = calculate_value_bets(
        {"home": prob_home, "draw": prob_draw, "away": prob_away}, best_odds)

    tab1, tab2, tab3 = st.tabs(["Основен анализ", "Разширена статистика", "AI Прогноза"])

    with tab1:
        st.metric("🏠 Шанс за домакин:", f"{prob_home*100:.1f}%")
        st.metric("⚖️ Шанс за равен:", f"{prob_draw*100:.1f}%")
        st.metric("✈️ Шанс за гост:", f"{prob_away*100:.1f}%")

    with tab2:
        st.write("### Статистика домакин:")
        st.json(home_stats)
        st.write("### Статистика гост:")
        st.json(away_stats)

    with tab3:
        if st.button("Генерирай AI прогноза"):
            prediction = predict_with_ai(home_stats, away_stats)
            if prediction is not None:
                st.write(f"Победа {match['home_team']}: {prediction[0]*100:.1f}%")
                st.write(f"Равенство: {prediction[1]*100:.1f}%")
                st.write(f"Победа {match['away_team']}: {prediction[2]*100:.1f}%")

if __name__ == "__main__":
    main()
    
