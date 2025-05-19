import streamlit as st
import pandas as pd
from scipy.stats import poisson

# Конфигурация с тестови данни
TEST_DATA = {
    "matches": [
        {
            "home_team": "Manchester City",
            "away_team": "Bournemouth",
            "odds": {"home": 1.30, "draw": 6.00, "away": 10.00},
            "stats": {
                "home_avg_goals": 2.8,
                "away_avg_goals": 1.1,
                "h2h": [3, 2, 4]  # Последни 3 срещи: голове домакин
            }
        },
        {
            "home_team": "Liverpool",
            "away_team": "Everton",
            "odds": {"home": 1.45, "draw": 4.50, "away": 7.50},
            "stats": {
                "home_avg_goals": 2.5,
                "away_avg_goals": 0.9,
                "h2h": [2, 1, 0]
            }
        }
    ]
}

def calculate_probabilities(home_avg, away_avg):
    """Изчислява вероятности чрез Poisson дистрибуция"""
    home_win, draw, away_win = 0, 0, 0
    for i in range(0, 6):
        for j in range(0, 6):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += p
            elif i == j: draw += p
            else: away_win += p
    return home_win, draw, away_win

def main():
    st.set_page_config(page_title="Value Bet Demo", layout="wide")
    st.title("🎯 Value Bet Анализатор [Демо]")
    
    # Избор на мач
    selected_match = st.selectbox(
        "Избери мач за анализ:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in TEST_DATA["matches"]]
    )
    
    # Намери данни за избрания мач
    match = next(m for m in TEST_DATA["matches"] if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)
    
    # Изчисли вероятности
    prob_home, prob_draw, prob_away = calculate_probabilities(
        match["stats"]["home_avg_goals"],
        match["stats"]["away_avg_goals"]
    )
    
    # Визуализация на резултатите
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(f"🏠 {match['home_team']}")
        st.metric("Средни голове", match["stats"]["home_avg_goals"])
        st.metric("Шанс за победа", f"{prob_home*100:.1f}%")
        st.metric("Коефициент", match["odds"]["home"])
        
    with col2:
        st.subheader("⚖ Равен")
        st.metric("Шанс", f"{prob_draw*100:.1f}%")
        st.metric("Коефициент", match["odds"]["draw"])
        
    with col3:
        st.subheader(f"✈ {match['away_team']}")
        st.metric("Средни голове", match["stats"]["away_avg_goals"])
        st.metric("Шанс за победа", f"{prob_away*100:.1f}%")
        st.metric("Коефициент", match["odds"]["away"])
    
    # Value Bet анализ
    st.divider()
    st.subheader("🔍 Value Bet Анализ")
    
    value_bets = []
    if prob_home > (1 / match["odds"]["home"]):
        value_bets.append(f"Победа {match['home_team']}")
    if prob_draw > (1 / match["odds"]["draw"]):
        value_bets.append("Равен")
    if prob_away > (1 / match["odds"]["away"]):
        value_bets.append(f"Победа {match['away_team']}")
    
    if value_bets:
        st.success(f"✅ Стойностни залози: {', '.join(value_bets)}")
    else:
        st.error("❌ Няма стойностни залози в този мач")
    
    # Графики
    st.divider()
    st.subheader("📊 Визуален анализ")
    
    col1, col2 = st.columns(2)
    with col1:
        chart_data = pd.DataFrame({
            "Тип": ["Домакин", "Равен", "Гост"],
            "Вероятност": [prob_home, prob_draw, prob_away]
        })
        st.bar_chart(chart_data, x="Тип", y="Вероятност")
    
    with col2:
        h2h_data = pd.DataFrame({
            "Срещи": ["Последна 1", "Последна 2", "Последна 3"],
            "Голове домакин": match["stats"]["h2h"]
        })
        st.line_chart(h2h_data.set_index("Срещи"))

if __name__ == "__main__":
    main()
