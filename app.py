import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib

# ================== КОНФИГУРАЦИЯ ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

# ================== API ФУНКЦИИ ================== #
@st.cache_data(ttl=3600)
def get_sports():
    try:
        response = requests.get("https://api.the-odds-api.com/v4/sports", params={"apiKey": ODDS_API_KEY})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Грешка при взимане на спортове: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_odds(sport_key):
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

TEAM_ID_MAPPING = {
    "Manchester City": 65,
    "AFC Bournemouth": 1044,
    "Liverpool": 64,
    "Everton": 62,
    "Arsenal": 57,
    "Tottenham Hotspur": 73,
    # ... добавете останалите отбори
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
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Грешка при взимане на статистики за {team_name}: {str(e)}")
        return None

# ================== АНАЛИТИЧНИ ФУНКЦИИ ================== #
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
        if odds[outcome] == 0:
            value[outcome] = -1  # Ако няма коефициент, стойността е отрицателна
        else:
            implied_prob = 1 / odds[outcome]
            value[outcome] = probabilities[outcome] - implied_prob
    return value

# ================== МАШИННО ОБУЧЕНИЕ ================== #
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

def process_team_stats(matches, is_home):
    if not matches:
        return {"avg_goals": 1.0, "win_rate": 0.5}
    goals = []
    wins = 0
    for m in matches[-10:]:
        score = m["score"]["fullTime"]
        if is_home:
            goals.append(score.get("home", 0))
            if score.get("home", 0) > score.get("away", 0):
                wins += 1
        else:
            goals.append(score.get("away", 0))
            if score.get("away", 0) > score.get("home", 0):
                wins += 1
    if len(matches) >= 10:
        win_rate = wins / 10
    elif len(matches) > 0:
        win_rate = wins / len(matches)
    else:
        win_rate = 0
    avg_goals = np.mean(goals) if goals else 1.0
    return {"avg_goals": avg_goals, "win_rate": win_rate}

# ================== ПОТРЕБИТЕЛСКИ ИНТЕРФЕЙС ================== #
def main():
    st.set_page_config(page_title="Advanced Bet Analyzer", layout="wide", page_icon="⚽")
    st.title("🔮 Advanced Bet Analyzer")

    # Взимаме спортове, филтрираме само футболни
    sports = get_sports()
    soccer_sports = {s["title"]: s["key"] for s in sports if s["group"] == "soccer"}

    if not soccer_sports:
        st.error("Няма намерени футболни първенства.")
        return

    selected_sport = st.selectbox("Избери първенство", list(soccer_sports.keys()))
    sport_key = soccer_sports[selected_sport]

    matches = get_odds(sport_key)
    if not matches:
        st.warning("Няма налични мачове в момента за избраното първенство.")
        return

    selected_match = st.selectbox(
        "Избери мач за анализ:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)

    home_stats_raw = get_team_stats(match["home_team"])
    away_stats_raw = get_team_stats(match["away_team"])

    # Проверка за налични статистики
    if home_stats_raw is None or away_stats_raw is None:
        st.warning("Няма достатъчно статистики за избраните отбори.")
        return

    home_stats = process_team_stats(home_stats_raw, is_home=True)
    away_stats = process_team_stats(away_stats_raw, is_home=False)

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], away_stats["avg_goals"]
    )

    # Взимаме най-добрите коефициенти за всеки изход
    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"].lower() == "draw"),
            "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
        }
    except Exception as e:
        st.error(f"Грешка при взимане на коефициенти: {str(e)}")
        best_odds = {"home": 0, "draw": 0, "away": 0}

    # Покажи коефициентите за debug
    st.write("**Най-добри коефициенти:**", best_odds)

    value_bets = calculate_value_bets(
        {"home": prob_home, "draw": prob_draw, "away": prob_away},
        best_odds
    )

    tab1, tab2, tab3 = st.tabs(["Основен анализ", "Разширена статистика", "AI Прогнози"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader(f"🏠 {match['home_team']}")
            st.metric("Средни голове", f"{home_stats['avg_goals']:.2f}")
            st.metric("Шанс за победа", f"{prob_home*100:.1f}%")
            st.metric("Value Score", f"{value_bets['home']*100:.1f}%", delta="Стойностен" if value_bets['home'] > 0 else "Нестойностен")

        with col2:
            st.subheader("⚖ Равен")
            st.metric("Шанс", f"{prob_draw*100:.1f}%")
            st.metric("Value Score", f"{value_bets['draw']*100:.1f}%", delta="Стойностен" if value_bets['draw'] > 0 else "Нестойностен")

        with col3:
            st.subheader(f"✈ {match['away_team']}")
            st.metric("Средни голове", f"{away_stats['avg_goals']:.2f}")
            st.metric("Шанс за победа", f"{prob_away*100:.1f}%")
            st.metric("Value Score", f"{value_bets['away']*100:.1f}%", delta="Стойностен" if value_bets['away'] > 0 else "Нестойностен")

    with tab2:
        st.subheader("📈 Исторически показатели")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Последни 5 мача {match['home_team']}:**")
            if home_stats_raw:
                for m in home_stats_raw[-5:]:
                    result = f"{m['score']['fullTime'].get('home', 0)}-{m['score']['fullTime'].get('away', 0)}"
                    st.write(f"- {result} ({m['utcDate'][:10]})")
        with col2:
            st.write(f"**Последни 5 мача {match['away_team']}:**")
            if away_stats_raw:
                for m in away_stats_raw[-5:]:
                    result = f"{m['score']['fullTime'].get('away', 0)}-{m['score']['fullTime'].get('home', 0)}"
                    st.write(f"- {result} ({m['utcDate'][:10]})")

    with tab3:
        st.subheader("🤖 AI Прогноза")
        if st.button("Генерирай прогноза"):
            ai_prediction = predict_with_ai(home_stats, away_stats)
            if ai_prediction is not None:
                st.write("### Вероятности:")
                st.write(f"- Победа {match['home_team']}: {ai_prediction[0]*100:.1f}%")
                st.write(f"- Равен: {ai_prediction[1]*100:.1f}%")
                st.write(f"- Победа {match['away_team']}: {ai_prediction[2]*100:.1f}%")

if __name__ == "__main__":
    main()
