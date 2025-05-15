import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Стойностни залози - Премачове", layout="wide")

# Заглавие
st.title("Стойностни залози - Премачове")
st.subheader("Извличане на стойностни залози от API в реално време (демо с фиктивни данни)")

# Избор на първенство
leagues = ["Английска Висша лига", "Испанска Ла Лига", "Германска Бундеслига", "Италианска Серия А"]
selected_league = st.selectbox("Избери първенство", leagues)

# Настройки на банката и целта
with st.expander("Настройки на банката"):
    initial_bankroll = st.number_input("Начална банка (лв)", value=500)
    goal_profit_percent = st.slider("Целева печалба (%)", 10, 100, 30)
    goal_days = st.number_input("Срок за постигане (дни)", min_value=1, value=5)
    dynamic_bet = st.checkbox("Изчислявай залога динамично според целта", value=True)

# Фиктивни данни (за демонстрация)
teams = ["Ливърпул", "Ман Сити", "Арсенал", "Челси", "Манчестър Юн", "Тотнъм"]
matches = []

for _ in range(10):
    home, away = random.sample(teams, 2)
    odds_home = round(random.uniform(1.5, 3.5), 2)
    model_prob = round(random.uniform(0.3, 0.7), 2)
    implied_prob = round(1 / odds_home, 2)
    value_pct = round((model_prob - implied_prob) * 100, 2)
    if value_pct > 5:
        matches.append({
            "Мач": f"{home} - {away}",
            "Коеф": odds_home,
            "Вер. по модел": f"{int(model_prob*100)}%",
            "Value %": f"{value_pct:.2f}%"
        })

# Прогнози
st.markdown("### Препоръчани стойностни залози за днес")
if matches:
    df = pd.DataFrame(matches)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Няма стойностни залози за момента. Опитай по-късно или смени първенството.")

# История и статистика (фиктивна за сега)
with st.expander("Статистика"):
    st.markdown(f"- Начална банка: **{initial_bankroll:.2f} лв**")
    st.markdown(f"- Целева печалба: **{goal_profit_percent}%** за **{goal_days} дни**")
    st.markdown("- ROI: **12.3%**")
    st.markdown("- Успеваемост: **61.5%**")
    st.markdown("- Нетна печалба: **+83.50 лв**")
