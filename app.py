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
BASE_FOOTBALL_URL = "https://api.football-data.org/v4"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports"

# Пълен списък на отбори
TEAM_IDS = {
    "Arsenal": 57, "Aston Villa": 58, "Bournemouth": 1044,
    "Brentford": 402, "Brighton": 397, "Burnley": 328,
    "Chelsea": 61, "Crystal Palace": 354, "Everton": 62,
    "Fulham": 63, "Liverpool": 64, "Luton": 389,
    "Manchester City": 65, "Manchester United": 66,
    "Newcastle United": 67, "Nottingham Forest": 351,
    "Sheffield United": 356, "Tottenham Hotspur": 73,
    "West Ham United": 563, "Wolverhampton Wanderers": 76
}

# ================== API HELPERS ================== #
def fetch_odds():
    """Вземи всички мачове и коефициенти"""
    try:
        response = requests.get(
            f"{ODDS_API_URL}/{SPORT}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            },
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Грешка при взимане на мачове: {str(e)}")
        return []

def fetch_team_matches(team_name):
    """Вземи последни 5 мача за отбор"""
    team_id = TEAM_IDS.get(team_name)
    if not team_id:
        return None
    
    try:
        response = requests.get(
            f"{BASE_FOOTBALL_URL}/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 5},
            timeout=15
        )
        response.raise_for_status()
        return response.json()["matches"]
    except Exception as e:
        st.error(f"Грешка при взимане на данни за {team_name}: {str(e)}")
        return None

# ================== АНАЛИТИЧНИ ФУНКЦИИ ================== #
def calculate_poisson_probability(home_avg, away_avg):
    """Изчисли вероятности с Poisson дистрибуция"""
    home_win = draw = away_win = 0.0
    
    for i in range(0, 6):
        for j in range(0, 6):
            prob = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_win += prob
            elif i == j:
                draw += prob
            else:
                away_win += prob
                
    return home_win, draw, away_win

def analyze_bookmakers(match_data):
    """Анализирай коефициентите от различни букмейкъри"""
    bookmakers_data = []
    
    for bookmaker in match_data.get("bookmakers", []):
        for outcome in bookmaker["markets"][0]["outcomes"]:
            bookmakers_data.append({
                "Bookmaker": bookmaker["title"],
                "Outcome": outcome["name"],
                "Odds": outcome["price"]
            })
    
    return pd.DataFrame(bookmakers_data)

# ================== ПОТРЕБИТЕЛСКИ ИНТЕРФЕЙС ================== #
def main():
    st.set_page_config(page_title="Real-Time Bet Analyzer", layout="wide")
    st.title("📊 Реален Анализатор на Залози")
    
    # Зареди мачове
    matches = fetch_odds()
    
    if not matches:
        st.warning("Няма налични мачове в момента")
        return
    
    # Избор на мач
    selected_match = st.selectbox(
        "Избери мач за анализ:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches],
        index=0
    )
    
    # Вземи данни за избрания мач
    match = next((m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match), None)
    if not match:
        st.error("Избраният мач не е намерен")
        return

    # Основен анализ
    with st.spinner("Анализираме мача..."):
        # Данни за отборите
        home_matches = fetch_team_matches(match["home_team"])
        away_matches = fetch_team_matches(match["away_team"])
        
        # Изчисли средни голове
        home_avg = np.mean([m["score"]["fullTime"]["home"] for m in home_matches]) if home_matches else 1.5
        away_avg = np.mean([m["score"]["fullTime"]["away"] for m in away_matches]) if away_matches else 1.0
        
        # Изчисли вероятности
        prob_home, prob_draw, prob_away = calculate_poisson_probability(home_avg, away_avg)
        
        # Визуализация
        tab1, tab2, tab3 = st.tabs(["Основен", "Статистики", "Коефициенти"])
        
        with tab1:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader(f"🏠 {match['home_team']}")
                st.metric("Средни голове", f"{home_avg:.2f}")
                st.metric("Шанс за победа", f"{prob_home*100:.1f}%")
            
            with col2:
                st.subheader("⚖ Равен")
                st.metric("Шанс", f"{prob_draw*100:.1f}%")
            
            with col3:
                st.subheader(f"✈ {match['away_team']}")
                st.metric("Средни голове", f"{away_avg:.2f}")
                st.metric("Шанс за победа", f"{prob_away*100:.1f}%")
        
        with tab2:
            st.subheader("📈 Детайлни статистики")
            
            col1, col2 = st.columns(2)
            with col1:
                if home_matches:
                    st.write(f"**Последни 5 мача {match['home_team']}:**")
                    for m in home_matches[-5:]:
                        score = f"{m['score']['fullTime']['home']}-{m['score']['fullTime']['away']}"
                        st.write(f"- {score} ({m['utcDate'][:10]})")
            
            with col2:
                if away_matches:
                    st.write(f"**Последни 5 мача {match['away_team']}:**")
                    for m in away_matches[-5:]:
                        score = f"{m['score']['fullTime']['away']}-{m['score']['fullTime']['home']}"
                        st.write(f"- {score} ({m['utcDate'][:10]})")
        
        with tab3:
            st.subheader("🔍 Сравнение на коефициенти")
            odds_df = analyze_bookmakers(match)
            if not odds_df.empty:
                st.dataframe(
                    odds_df,
                    column_config={
                        "Odds": st.column_config.NumberColumn(
                            format="%.2f",
                            help="Най-добри коефициенти"
                        )
                    },
                    hide_index=True
                )
            else:
                st.warning("Няма данни за коефициенти")

if __name__ == "__main__":
    main()
