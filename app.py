import streamlit as st
import requests
import numpy as np
from scipy.stats import poisson
import joblib
from datetime import datetime

# --- Конфигурация и ключове ---
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

# --- Зареждане на live odds ---
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
        st.error(f"Грешка при зареждане на odds: {e}")
        return []

# --- Зареждане на статистики за отбор ---
@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        st.warning(f"Неизвестен отбор: {team_name}")
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
        st.error(f"Грешка при зареждане на статистики за {team_name}: {e}")
        return []

# --- Изчисляване на вероятности с поасоново разпределение ---
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

# --- Извличане на основни статистики от мачовете ---
def get_team_stats_data(matches, is_home=True):
    if not matches:
        # Фалбек стойности, ако няма данни
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

# --- Зареждане на ML модел и скейлър ---
def load_ml_artifacts():
    try:
        model = joblib.load("model.pkl")
        scaler = joblib.load("scaler.pkl")
        return model, scaler
    except Exception as e:
        st.error(f"Грешка при зареждане на ML артефакти: {e}")
        return None, None

# --- Основна функция ---
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    matches = get_live_odds()
    if not matches:
        st.warning("Няма налични мачове")
        return

    selected_match = st.selectbox(
        "Избери мач:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)

    home_matches_raw = get_team_stats(match["home_team"])
    away_matches_raw = get_team_stats(match["away_team"])

    home_stats = get_team_stats_data(home_matches_raw, is_home=True)
    away_stats = get_team_stats_data(away_matches_raw, is_home=False)

    # Определяне на най-добрите коефициенти
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
        pass  # Ако има проблеми с odds, ползва фалбек стойности

    # Изчисляване на вероятности
    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"],
        away_stats["avg_goals"]
    )

    # Показване на резултатите
    st.subheader("Резултати от анализ")
    col1, col2, col3 = st.columns(3)

    col1.metric("Вероятност за победа на домакина", f"{prob_home*100:.1f}%")
    col2.metric("Вероятност за равенство", f"{prob_draw*100:.1f}%")
    col3.metric("Вероятност за победа на госта", f"{prob_away*100:.1f}%")

    st.subheader("Най-добри коефициенти")
    col1.metric("Коефициент за домакин", f"{best_odds['home']:.2f}")
    col2.metric("Коефициент за равенство", f"{best_odds['draw']:.2f}")
    col3.metric("Коефициент за гост", f"{best_odds['away']:.2f}")

if __name__ == "__main__":
    main()
