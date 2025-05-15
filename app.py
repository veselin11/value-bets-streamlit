import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import math

# Конфигурация
local_tz = pytz.timezone("Europe/Sofia")
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# ===== Настройки =====
with tabs[2]:
    st.header("Настройки")
    col1, col2, col3 = st.columns(3)
    with col1:
        target_profit = st.number_input("Целева печалба (лв)", value=150)
    with col2:
        days = st.number_input("Целеви дни", value=5)
    with col3:
        bank = st.number_input("Начална банка (лв)", value=500)

    daily_profit_goal = target_profit / days
    st.info(f"Дневна цел: {round(daily_profit_goal, 2)} лв")

# ===== Прогнози (демо) =====
with tabs[0]:
    st.title("Стойностни залози – Демонстрация")
    st.caption("Данни: примерни стойности (без API)")

    demo_data = [
        {
            "Мач": "Барселона vs Реал Мадрид",
            "Пазар": "H2H: Барселона",
            "Коефициент": 2.50,
            "Value %": 12.5,
            "Букмейкър": "Bet365",
            "Час": "21:00",
            "Мач ID": "1"
        },
        {
            "Мач": "Ливърпул vs Манчестър Сити",
            "Пазар": "BTTS: Yes",
            "Коефициент": 1.90,
            "Value %": 7.8,
            "Букмейкър": "Betfair",
            "Час": "18:30",
            "Мач ID": "2"
        },
        {
            "Мач": "Ювентус vs Интер",
            "Пазар": "Over/Under 2.5: Over",
            "Коефициент": 2.10,
            "Value %": 9.6,
            "Букмейкър": "Pinnacle",
            "Час": "20:00",
            "Мач ID": "3"
        }
    ]

    df = pd.DataFrame(demo_data)
    df["Избери"] = False
    selected_rows = []

    st.markdown("### Примерни стойностни залози")
    for i, row in df.iterrows():
        with st.expander(f"{row['Мач']} — {row['Пазар']}"):
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**Коефициент:** {row['Коефициент']}")
                st.markdown(f"**Value %:** `{row['Value %']}`")
                st.markdown(f"**Букмейкър:** {row['Букмейкър']}")
                st.markdown(f"**Час:** {row['Час']}")
            with col2:
                selected = st.checkbox("Залагай", key=row["Мач ID"])
                if selected:
                    selected_rows.append(row)
            with col3:
                stake = st.number_input(
                    label="Сума на залог (лв)",
                    key=f"stake_{row['Мач ID']}",
                    min_value=0,
                    value=int(round((daily_profit_goal / (row["Коефициент"] - 1)) / 10.0) * 10)
                )

    if selected_rows:
        st.subheader("Избрани залози:")
        summary = []
        total_stake = 0
        for row in selected_rows:
            stake = st.session_state.get(f"stake_{row['Мач ID']}", 0)
            total_stake += stake
            summary.append({
                "Мач": row["Мач"],
                "Пазар": row["Пазар"],
                "Коефициент": row["Коефициент"],
                "Value %": row["Value %"],
                "Сума на залог": stake
            })
        st.dataframe(pd.DataFrame(summary))
        st.success(f"Обща сума за залагане: {total_stake} лв")
    else:
        st.info("Не са избрани залози.")

# ===== История (празна) =====
with tabs[1]:
    st.header("История на залози (в разработка)")
