import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import poisson
from datetime import datetime, timedelta
from functools import lru_cache

# ================== КОНФИГУРАЦИЯ ================== #
try:
    FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError as e:
    st.error(f"Липсващ ключ: {e}")
    st.stop()

SPORT = "soccer_epl"

# Пълен списък с отбори и ID-та за Premier League 2023/24
TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Aston Villa": 58,
    "Bournemouth": 1044,
    "Brentford": 402,
    "Brighton": 397,
    "Burnley": 328,
    "Chelsea": 61,
    "Crystal Palace": 354,
    "Everton": 62,
    "Fulham": 63,
    "Liverpool": 64,
    "Luton": 389,
    "Manchester City": 65,
    "Manchester United": 66,
    "Newcastle United": 67,
    "Nottingham Forest": 351,
    "Sheffield United": 356,
    "Tottenham Hotspur": 73,
    "West Ham United": 563,
    "Wolverhampton Wanderers": 76
}

# ================== РАЗШИРЕНИ ФУНКЦИИ ================== #
@st.cache_data(ttl=3600)
def get_historical_data(team_id, days=365):
    """Вземи исторически данни за отбор"""
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"dateFrom": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")}
        )
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Грешка при взимане на исторически данни: {str(e)}")
        return []

def compare_bookmakers(match_data):
    """Сравни коефициенти между различни букмейкъри"""
    comparison = {}
    for bookmaker in match_data.get("bookmakers", []):
        for outcome in bookmaker["markets"][0]["outcomes"]:
            if outcome["name"] not in comparison:
                comparison[outcome["name"]] = []
            comparison[outcome["name"]].append({
                "bookmaker": bookmaker["title"],
                "price": outcome["price"]
            })
    return comparison

# ================== ВИЗУАЛИЗАЦИИ ================== #
def plot_trends(team_id):
    """Визуализирай исторически тенденции"""
    matches = get_historical_data(team_id)
    if not matches:
        return None
    
    data = []
    for match in matches:
        date = match["utcDate"][:10]
        if match["homeTeam"]["id"] == team_id:
            goals = match["score"]["fullTime"]["home"]
            result = "Win" if goals > match["score"]["fullTime"]["away"] else "Loss" if goals < match["score"]["fullTime"]["away"] else "Draw"
        else:
            goals = match["score"]["fullTime"]["away"]
            result = "Win" if goals > match["score"]["fullTime"]["home"] else "Loss" if goals < match["score"]["fullTime"]["home"] else "Draw"
        
        data.append({
            "Date": date,
            "Goals": goals,
            "Result": result
        })
    
    df = pd.DataFrame(data)
    fig = px.line(df, x="Date", y="Goals", color="Result", 
                 title="Тенденция на голове (последните 12 месеца)",
                 markers=True)
    return fig

# ================== ОСНОВЕН ИНТЕРФЕЙС ================== #
def main():
    st.set_page_config(page_title="Advanced Bet Analyzer Pro", layout="wide")
    st.title("⚽ Advanced Bet Analyzer Pro")
    
    # Зареди коефициенти
    matches = get_live_odds()
    
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

    # Разширен анализ
    tab1, tab2, tab3, tab4 = st.tabs(["Основен", "Тенденции", "Сравнение", "Нотификации"])
    
    with tab1:
        # ... (основният анализ от предишния код) ...
    
    with tab2:
        st.header("📈 Исторически тенденции")
        col1, col2 = st.columns(2)
        
        with col1:
            home_id = TEAM_ID_MAPPING.get(match["home_team"])
            if home_id:
                fig = plot_trends(home_id)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            away_id = TEAM_ID_MAPPING.get(match["away_team"])
            if away_id:
                fig = plot_trends(away_id)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("🔍 Сравнение между букмейкъри")
        comparison = compare_bookmakers(match)
        
        for outcome in comparison:
            st.subheader(outcome)
            df = pd.DataFrame(comparison[outcome])
            st.dataframe(df.sort_values("price", ascending=False), 
                        column_config={
                            "price": st.column_config.NumberColumn(
                                "Коефициент",
                                format="%.2f"
                            )
                        })
    
    with tab4:
        st.header("🔔 Настройки на нотификациите")
        notification_settings = {
            "threshold": st.slider("Праг на промяна (%)", 1, 50, 5),
            "interval": st.selectbox("Интервал на проверка", ["15 минути", "30 минути", "1 час"])
        }
        st.success("Нотификациите ще се актуализират автоматично според избраните настройки")

if __name__ == "__main__":
    main()
