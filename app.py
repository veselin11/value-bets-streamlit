import streamlit as st
import pandas as pd
from scipy.stats import poisson

# Тестови данни (ако API не работи)
TEST_MATCHES = [
    {
        "home_team": "Manchester City",
        "away_team": "Bournemouth",
        "bookmakers": [{
            "markets": [{
                "outcomes": [
                    {"name": "Manchester City", "price": 1.3},
                    {"name": "Bournemouth", "price": 10.0}
                ]
            }]
        }]
    }
]

# Ръчен mapping на отбори (име -> средни голове)
TEAM_STATS = {
    "Manchester City": {"avg_goals": 2.5, "form": [3,2,1,2,3]},
    "Bournemouth": {"avg_goals": 1.1, "form": [0,1,1,0,1]},
}

def calculate_poisson_prob(home_avg, away_avg):
    """Изчисли вероятности чрез Poisson"""
    home_win, draw, away_win = 0, 0, 0
    for i in range(0, 6):
        for j in range(0, 6):
            prob = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += prob
            elif i == j: draw += prob
            else: away_win += prob
    return home_win, draw, away_win

# Streamlit интерфейс
st.set_page_config(page_title="Value Bet Tester", layout="wide")
st.title("⚡ Тестов анализатор [DEMO]")

selected_match = st.selectbox("Избери тестов мач", [
    "Manchester City vs Bournemouth"
])

# Анализ на мача
home_team, away_team = selected_match.split(" vs ")
home_stats = TEAM_STATS.get(home_team, {"avg_goals": 1.5})
away_stats = TEAM_STATS.get(away_team, {"avg_goals": 1.0})

prob_home, prob_draw, prob_away = calculate_poisson_prob(
    home_stats["avg_goals"], 
    away_stats["avg_goals"]
)

# Покажи резултатите
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(f"🏠 {home_team}")
    st.metric("Средни голове", home_stats["avg_goals"])
    st.metric("Шанс за победа", f"{prob_home*100:.1f}%")

with col2:
    st.subheader("⚖ Равен")
    st.metric("Шанс", f"{prob_draw*100:.1f}%")

with col3:
    st.subheader(f"✈ {away_team}")
    st.metric("Средни голове", away_stats["avg_goals"])
    st.metric("Шанс за победа", f"{prob_away*100:.1f}%")

# Value Bet анализ
best_odds = 1.3 # Примерен коефициент
implied_prob = (1 / best_odds) * 100
value = "✅ VALUE BET" if (prob_home*100) > implied_prob else "❌ Няма стойност"

st.divider()
st.subheader(f"Анализ: {value}")
st.write(f"**Коефициент за победа**: {best_odds:.2f}")
st.write(f"Ваша вероятност: {prob_home*100:.1f}% vs Имплицитна: {implied_prob:.1f}%")

# Графика
chart_data = pd.DataFrame({
    "Вероятност": [prob_home, prob_draw, prob_away],
    "Тип": ["Домакин", "Равен", "Гост"]
})
st.bar_chart(chart_data, x="Тип", y="Вероятност")
