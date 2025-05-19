import streamlit as st
import requests
import pandas as pd
from scipy.stats import poisson
from functools import lru_cache

# Конфигурация
FOOTBALL_DATA_API_KEY = "cb4a5917231d8b20dd6b85ae9d025e6e"
ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
LEAGUE = "PL"  # Английска Висша лига

# --- API функции (кеширани за бързодействие) ---
@lru_cache(maxsize=32)
def get_team_id(team_name):
    """Намери ID на отбор по име"""
    try:
        response = requests.get(
            "https://api.football-data.org/v4/teams",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"name": team_name}
        )
        return response.json()["teams"][0]["id"] if response.ok else None
    except:
        return None

@lru_cache(maxsize=32)
def get_football_stats(team_id):
    """Вземи последни 5 мача на отбор"""
    try:
        url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
        response = requests.get(url, headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY})
        return response.json()["matches"] if response.ok else []
    except:
        return []

@lru_cache(maxsize=32)
def get_h2h_stats(home_id, away_id):
    """Вземи H2H статистика между два отбора"""
    try:
        url = f"https://api.football-data.org/v4/teams/{home_id}/matches?vs={away_id}"
        response = requests.get(url, headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY})
        return response.json()["matches"] if response.ok else []
    except:
        return []

@lru_cache(maxsize=32)
def get_odds():
    """Вземи коефициенти от The Odds API"""
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    response = requests.get("https://api.the-odds-api.com/v4/sports/soccer_epl/odds", params=params)
    return response.json() if response.ok else []

# --- Изчисления ---
def calculate_poisson_prob(home_avg, away_avg):
    """Изчисли вероятности чрез Poisson дистрибуция"""
    home_win, draw, away_win = 0, 0, 0
    for i in range(0, 6):
        for j in range(0, 6):
            prob = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += prob
            elif i == j: draw += prob
            else: away_win += prob
    return home_win, draw, away_win

def analyze_team_form(matches, team_id):
    """Анализ на формата на отбора (последни 5 мача)"""
    goals_scored = []
    for match in matches:
        if match["homeTeam"]["id"] == team_id:
            goals_scored.append(match["score"]["fullTime"]["home"] or 0)
        else:
            goals_scored.append(match["score"]["fullTime"]["away"] or 0)
    return sum(goals_scored) / len(goals_scored) if goals_scored else 0

# --- Streamlit интерфейс ---
st.set_page_config(page_title="Value Bet Finder", layout="wide")
st.title("⚽ Value Bet Analyzer")

# Зареди данни
matches = get_odds()
if not matches:
    st.error("❌ Няма налични мачове или грешка при връзка с API")
    st.stop()

# Избор на мач
selected_match = st.selectbox("Избери мач", [f'{m["home_team"]} vs {m["away_team"]}' for m in matches])
match_data = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
home_team = match_data["home_team"]
away_team = match_data["away_team"]

# Вземи IDs
home_id = get_team_id(home_team)
away_id = get_team_id(away_team)

if not home_id or not away_id:
    st.error("❌ Отборът не е намерен във Football-Data.org")
    st.stop()

# Събери статистики
home_matches = get_football_stats(home_id)
away_matches = get_football_stats(away_id)
h2h_matches = get_h2h_stats(home_id, away_id)

# Изчисли средни голове
home_avg = analyze_team_form(home_matches[-5:], home_id) if home_matches else 1.2
away_avg = analyze_team_form(away_matches[-5:], away_id) if away_matches else 0.9

# Poisson вероятности
prob_home, prob_draw, prob_away = calculate_poisson_prob(home_avg, away_avg)

# Коефициенти
best_home_odds = max(
    outcome["price"] 
    for bookmaker in match_data["bookmakers"] 
    for outcome in bookmaker["markets"][0]["outcomes"] 
    if outcome["name"] == home_team
)

# Value Bet проверка
implied_prob_home = 1 / best_home_odds
value_bet = "✅ VALUE BET" if prob_home > implied_prob_home else "❌ Няма стойност"

# Покажи резултатите
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(f"🏠 {home_team}")
    st.metric("Средни голове (последни 5)", round(home_avg, 2))
    st.metric("Шанс за победа", f"{prob_home*100:.1f}%")

with col2:
    st.subheader("⚖ Равен")
    st.metric("Шанс за равенство", f"{prob_draw*100:.1f}%")

with col3:
    st.subheader(f"✈ {away_team}")
    st.metric("Средни голове (последни 5)", round(away_avg, 2))
    st.metric("Шанс за победа", f"{prob_away*100:.1f}%")

# Value Bet анализ
st.divider()
st.subheader(f"Анализ: {value_bet}")
st.write(f"**Най-добър коефициент за {home_team}**: {best_home_odds:.2f} (Имплицитна вероятност: {implied_prob_home*100:.1f}%)")

# Графика
chart_data = pd.DataFrame({
    "Тип": ["Домакин", "Равен", "Гост"],
    "Вероятност": [prob_home, prob_draw, prob_away]
})
st.bar_chart(chart_data, x="Тип", y="Вероятност", use_container_width=True)

# H2H история
if h2h_matches:
    st.subheader("Последни срещи между отборите")
    for match in h2h_matches[-3:]:
        result = (
            f"{match['score']['fullTime']['home']}-{match['score']['fullTime']['away']}"
            if match["homeTeam"]["id"] == home_id 
            else f"{match['score']['fullTime']['away']}-{match['score']['fullTime']['home']}"
        )
        st.write(f"- {result} ({match['utcDate'][:10]})")
