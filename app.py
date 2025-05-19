import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson

# Конфигурация
FOOTBALL_DATA_API_KEY = "tvoj_football_data_key"
ODDS_API_KEY = "tvoj_odds_api_key"
LEAGUE = "PL"  # Пример за Английска Висша лига (PL)

# --- Функции за данни ---
def get_football_stats(team_name):
    """Вземи исторически данни за отбор от Football-Data.org"""
    url = f"https://api.football-data.org/v4/teams/{team_name}/matches"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_odds():
    """Вземи коефициенти от The Odds API"""
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    params = {"apiKey": ODDS_API_KEY, "regions": "eu"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# --- Изчисления ---
def calculate_poisson_prob(home_avg, away_avg):
    """Изчисли вероятности за победа/равенство/загуба чрез Poisson"""
    home_win = 0
    draw = 0
    away_win = 0
    
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

# --- Streamlit UI ---
st.title("🔍 Value Bet Finder")
st.markdown("Анализирай мачове за стойностни залози на база статистика и коефициенти")

# Въвеждане на API ключове
with st.sidebar:
    st.header("🔑 API Настройки")
    odds_api_key = st.text_input("The Odds API Key", type="password")
    football_api_key = st.text_input("Football-Data.org Key", type="password")

if odds_api_key and football_api_key:
    # Зареди данни
    matches = get_odds()
    
    if matches:
        # Избор на мач
        match_names = [f"{m['home_team']} vs {m['away_team']}" for m in matches]
        selected_match = st.selectbox("Избери мач", match_names)
        
        # Намери избрания мач
        match_data = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)
        home_team = match_data['home_team']
        away_team = match_data['away_team']
        
        # Вземи статистики
        home_stats = get_football_stats(home_team)
        away_stats = get_football_stats(away_team)
        
        # Примерни данни (реално трябва да се обработят статистиките)
        home_avg_goals = 1.4
        away_avg_goals = 1.1
        
        # Изчисли вероятности
        prob_home, prob_draw, prob_away = calculate_poisson_prob(home_avg_goals, away_avg_goals)
        
        # Намери най-добрите коефициенти
        best_home_odds = max([o['price'] for bookmaker in match_data['bookmakers'] 
                            for o in bookmaker['markets'][0]['outcomes'] 
                            if o['name'] == home_team])
        
        # Покажи резултатите
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏠 Домакин", f"{prob_home*100:.1f}%")
            st.metric("Коефициент", f"{best_home_odds:.2f}")
            
        with col2:
            st.metric("⚖ Равен", f"{prob_draw*100:.1f}%")
            
        with col3:
            st.metric("✈ Гост", f"{prob_away*100:.1f}%")
        
        # Value Bet логика
        implied_prob_home = 1 / best_home_odds
        value_home = "✅" if prob_home > implied_prob_home else "❌"
        
        st.subheader("Value Bet Анализ")
        st.write(f"Победа {home_team}: {value_home} (Ваша вероятност: {prob_home*100:.1f}% vs Имплицитна: {implied_prob_home*100:.1f}%)")
        
        # Графика
        chart_data = pd.DataFrame({
            "Вероятност": [prob_home, prob_draw, prob_away],
            "Тип": ["Домакин", "Равен", "Гост"]
        })
        st.bar_chart(chart_data, x="Тип", y="Вероятност")
        
    else:
        st.error("Грешка при зареждане на мачове. Провери API ключовете.")
else:
    st.warning("Моля, въведи API ключовете в лявата колона.")
