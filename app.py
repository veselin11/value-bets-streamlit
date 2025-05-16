import streamlit as st
import pandas as pd
import numpy as np
import random

# Конфигурация на страницата
st.set_page_config(page_title="Value Залози", layout="wide")
st.title("Прогнози със стойност (Value Bets)")

# Настройки от страничния панел
st.sidebar.header("Настройки на залозите")
bank = st.sidebar.number_input("Начална банка (лв)", value=500)
min_value_threshold = st.sidebar.slider("Минимален value %", 5, 50, 10)

# Генериране на фиктивни мачове с value
@st.cache_data
def генерирай_прогнози(n=15):
    отбори = ["Левски", "ЦСКА", "Лудогорец", "Берое", "Ботев", "Славия", "Черно море", "Арда"]
    мачове = []
    for _ in range(n):
        home, away = random.sample(отбори, 2)
        p_home = np.clip(np.random.normal(0.45, 0.1), 0.2, 0.7)
        p_draw = np.clip(1 - p_home - np.random.uniform(0.15, 0.25), 0.1, 0.4)
        p_away = 1 - p_home - p_draw

        odds_home = round(1 / p_home + random.uniform(0.1, 0.6), 2)
        odds_draw = round(1 / p_draw + random.uniform(0.1, 0.6), 2)
        odds_away = round(1 / p_away + random.uniform(0.1, 0.6), 2)

        value_home = round((odds_home * p_home - 1) * 100, 2)
        value_draw = round((odds_draw * p_draw - 1) * 100, 2)
        value_away = round((odds_away * p_away - 1) * 100, 2)

        мачове.append({
            "Мач": f"{home} vs {away}",
            "Залог": "1",
            "Коеф": odds_home,
            "Шанс": round(p_home * 100, 1),
            "Value %": value_home
        })
        мачове.append({
            "Мач": f"{home} vs {away}",
            "Залог": "X",
            "Коеф": odds_draw,
            "Шанс": round(p_draw * 100, 1),
            "Value %": value_draw
        })
        мачове.append({
            "Мач": f"{home} vs {away}",
            "Залог": "2",
            "Коеф": odds_away,
            "Шанс": round(p_away * 100, 1),
            "Value %": value_away
        })
    df = pd.DataFrame(мачове)
    return df[df["Value %"] >= min_value_threshold]

# Зареждане на прогнозите
df = генерирай_прогнози()

# Извеждане
st.subheader("Най-добри прогнози")
st.dataframe(df.sort_values("Value %", ascending=False).reset_index(drop=True), use_container_width=True)

# Статистика в страничния панел
st.sidebar.markdown(f"Общо прогнози: {len(df)}")
if len(df) > 0:
    st.sidebar.markdown(f"Среден value %: {round(df['Value %'].mean(), 2)}")
    
