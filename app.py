import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
from functools import lru_cache

# ================== КОНФИГУРАЦИЯ ================== #
try:
    FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError as e:
    st.error(f"Липсващ ключ: {e}. Проверете secrets.toml файла!")
    st.stop()

SPORT = "soccer_epl"
TEAM_ID_MAPPING = {
    "Manchester City": 65,
    "AFC Bournemouth": 1044,
    "Liverpool": 64,
    "Everton": 62,
    "Arsenal": 57,
    "Tottenham Hotspur": 73,
}

# ================== API ФУНКЦИИ ================== #
@st.cache_data(ttl=3600)
def get_live_odds():
    """Вземи реални коефициенти от The Odds API"""
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json() or []
    except Exception as e:
        st.error(f"Грешка при взимане на коефициенти: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    """Вземи статистики за отбор"""
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return []
    
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 5},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Грешка при взимане на данни за {team_name}: {str(e)}")
        return []

# ================== АНАЛИТИЧНИ ФУНКЦИИ ================== #
def safe_mean(data, default=0.0):
    """Безопасно изчисляване на средна стойност"""
    return np.mean(data).item() if data else default

def calculate_poisson_probabilities(home_avg, away_avg):
    """Изчисли вероятности с Poisson дистрибуция"""
    home_win, draw, away_win = 0.0, 0.0, 0.0
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

# ================== ПОТРЕБИТЕЛСКИ ИНТЕРФЕЙС ================== #
def main():
    st.set_page_config(page_title="Advanced Bet Analyzer", layout="wide")
    st.title("🔮 Advanced Bet Analyzer")
    
    # Зареди коефициенти
    matches = get_live_odds()
    
    if not matches:
        st.warning("Няма налични мачове в момента")
        return
    
    # Избор на мач
    try:
        selected_match = st.selectbox(
            "Избери мач за анализ:",
            [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
        )
        match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    except StopIteration:
        st.error("Грешка при избор на мач")
        return

    # Вземи статистики
    home_stats_raw = get_team_stats(match["home_team"])
    away_stats_raw = get_team_stats(match["away_team"])
    
    # Обработка на статистиките
    home_goals = [m["score"]["fullTime"]["home"] for m in home_stats_raw if m["score"]["fullTime"]["home"] is not None]
    away_goals = [m["score"]["fullTime"]["away"] for m in away_stats_raw if m["score"]["fullTime"]["away"] is not None]
    
    home_stats = {
        "avg_goals": safe_mean(home_goals, 1.2),
        "win_rate": safe_mean([1 if h > a else 0 for h, a in zip(home_goals, away_goals)], 0.5)
    }
    
    away_stats = {
        "avg_goals": safe_mean(away_goals, 0.9),
        "win_rate": safe_mean([1 if a > h else 0 for h, a in zip(home_goals, away_goals)], 0.3)
    }
    
    # Изчисли вероятности
    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"],
        away_stats["avg_goals"]
    )
    
    # Визуализация
    tab1, tab2 = st.tabs(["Основен анализ", "История"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader(f"🏠 {match['home_team']}")
            st.metric("Средни голове", f"{home_stats['avg_goals']:.2f}")
            st.metric("Шанс за победа", f"{prob_home*100:.1f}%")
        
        with col2:
            st.subheader("⚖ Равен")
            st.metric("Шанс", f"{prob_draw*100:.1f}%")
        
        with col3:
            st.subheader(f"✈ {match['away_team']}")
            st.metric("Средни голове", f"{away_stats['avg_goals']:.2f}")
            st.metric("Шанс за победа", f"{prob_away*100:.1f}%")
    
    with tab2:
        st.subheader("📈 Исторически показатели")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Последни 5 мача {match['home_team']}:**")
            if home_stats_raw:
                for m in home_stats_raw[-5:]:
                    score = m["score"]["fullTime"]
                    st.write(f"- {score['home']}-{score['away']} ({m['utcDate'][:10]})")
            else:
                st.warning("Няма исторически данни")
        
        with col2:
            st.write(f"**Последни 5 мача {match['away_team']}:**")
            if away_stats_raw:
                for m in away_stats_raw[-5:]:
                    score = m["score"]["fullTime"]
                    st.write(f"- {score['away']}-{score['home']} ({m['utcDate'][:10]})")
            else:
                st.warning("Няма исторически данни")

if __name__ == "__main__":
    main()
