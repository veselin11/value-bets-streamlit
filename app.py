import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import poisson
from datetime import datetime, timedelta

# ================== КОНФИГУРАЦИЯ ================== #
try:
    FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError as e:
    st.error(f"Липсващ ключ: {e}")
    st.stop()

SPORT = "soccer_epl"

TEAM_ID_MAPPING = {
    "Arsenal": 57, "Aston Villa": 58, "Bournemouth": 1044,
    "Brentford": 402, "Brighton": 397, "Burnley": 328,
    "Chelsea": 61, "Crystal Palace": 354, "Everton": 62,
    "Fulham": 63, "Liverpool": 64, "Luton": 389,
    "Manchester City": 65, "Manchester United": 66,
    "Newcastle United": 67, "Nottingham Forest": 351,
    "Sheffield United": 356, "Tottenham Hotspur": 73,
    "West Ham United": 563, "Wolverhampton Wanderers": 76
}

# ================== ФУНКЦИИ ЗА ДАННИ ================== #
@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    """Вземи статистики за отбор"""
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return None
    
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 5}
        )
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Грешка при взимане на данни: {str(e)}")
        return []

def calculate_probabilities(home_avg, away_avg):
    """Изчисли вероятности с Poisson дистрибуция"""
    home_win, draw, away_win = 0.0, 0.0, 0.0
    for i in range(0, 6):
        for j in range(0, 6):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            home_win += p if i > j else 0
            draw += p if i == j else 0
            away_win += p if i < j else 0
    return home_win, draw, away_win

# ================== ИНТЕРФЕЙС ================== #
def main():
    st.set_page_config(page_title="Bet Analyzer Pro", layout="wide")
    st.title("⚽ Пълен Анализатор за Залози")
    
    # Зареди мачове
    try:
        matches = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
            params={"apiKey": ODDS_API_KEY, "regions": "eu"}
        ).json()
    except Exception as e:
        st.error(f"Грешка при зареждане на мачове: {str(e)}")
        return

    if not matches:
        st.warning("Няма налични мачове в момента")
        return

    # Избор на мач
    selected_match = st.selectbox(
        "Избери мач за анализ:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    
    try:
        match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    except StopIteration:
        st.error("Грешка при избор на мач")
        return

    # Основен анализ
    tab1, tab2, tab3 = st.tabs(["Статистики", "Тенденции", "Сравнение"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        # Домакин
        with col1:
            st.subheader(f"🏠 {match['home_team']}")
            home_stats = get_team_stats(match["home_team"])
            if home_stats:
                avg_goals = np.mean([m["score"]["fullTime"]["home"] for m in home_stats])
                st.metric("Средни голове (последни 5 мача)", f"{avg_goals:.2f}")
            else:
                st.warning("Няма данни за домакина")

        # Равен 
        with col2:
            st.subheader("⚖ Общ анализ")
            if home_stats and 'away_team' in match:
                home_avg = np.mean([m["score"]["fullTime"]["home"] for m in home_stats])
                away_stats = get_team_stats(match["away_team"])
                away_avg = np.mean([m["score"]["fullTime"]["away"] for m in away_stats]) if away_stats else 0
                prob_home, prob_draw, prob_away = calculate_probabilities(home_avg, away_avg)
                
                st.metric("Шанс за победа домакин", f"{prob_home*100:.1f}%")
                st.metric("Шанс за равен", f"{prob_draw*100:.1f}%")
                st.metric("Шанс за победа гост", f"{prob_away*100:.1f}%")

        # Гост
        with col3:
            st.subheader(f"✈ {match['away_team']}")
            away_stats = get_team_stats(match["away_team"])
            if away_stats:
                avg_goals = np.mean([m["score"]["fullTime"]["away"] for m in away_stats])
                st.metric("Средни голове (последни 5 мача)", f"{avg_goals:.2f}")
            else:
                st.warning("Няма данни за гост")

    with tab2:
        st.header("📊 Исторически Тенденции")
        # Добавете код за графики тук...

    with tab3:
        st.header("🔍 Сравнение на Коефициенти")
        # Добавете код за сравнение тук...

if __name__ == "__main__":
    main()
