import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import math

# === Конфигурация ===
local_tz = pytz.timezone("Europe/Sofia")
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# Сесийна история на залозите
if "bet_history" not in st.session_state:
    st.session_state.bet_history = []

# === Настройки ===
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

# === Прогнози (демо) ===
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
    selected_rows = []

    st.markdown("### Предложени стойностни залози")
    for i, row in df.iterrows():
        with st.expander(f"{row['Мач']} — {row['Пазар']}"):
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**Коефициент:** `{row['Коефициент']}`")
                st.markdown(f"**Value %:** `{row['Value %']}`")
                st.markdown(f"**Букмейкър:** {row['Букмейкър']}")
                st.markdown(f"**Час:** {row['Час']}")
            with col2:
                selected = st.checkbox("Залагай", key=row["Мач ID"])
                if selected:
                    selected_rows.append(row)
            with col3:
                stake_default = int(round((daily_profit_goal / (row["Коефициент"] - 1)) / 10.0) * 10)
                stake = st.number_input(
                    "Сума на залог (лв)",
                    min_value=10,
                    step=10,
                    value=stake_default,
                    key=f"stake_{row['Мач ID']}"
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
                "Сума на залог": stake,
                "Дата": datetime.now(local_tz).strftime("%Y-%m-%d %H:%M"),
                "Резултат": "",  # За по-късно въвеждане
                "Печалба/Загуба": ""
            })
        st.dataframe(pd.DataFrame(summary))
        st.success(f"Обща сума за залагане: {total_stake} лв")

        # Запис в историята
        if st.button("Запиши в история"):
            st.session_state.bet_history.extend(summary)
            st.success("Залозите са записани в историята.")
    else:
        st.info("Не са избрани залози.")

# === История ===
with tabs[1]:
    st.header("История на залозите")

    if not st.session_state.bet_history:
        st.info("Няма записани залози.")
    else:
        df_hist = pd.DataFrame(st.session_state.bet_history)

        for i in range(len(df_hist)):
            df_hist.at[i, "Резултат"] = st.text_input(
                f"Резултат за {df_hist.at[i, 'Мач']} ({df_hist.at[i, 'Пазар']})",
                value=df_hist.at[i, "Резултат"],
                key=f"result_{i}"
            )

            try:
                result = df_hist.at[i, "Резултат"].lower()
                stake = df_hist.at[i, "Сума на залог"]
                odd = df_hist.at[i, "Коефициент"]
                if "печели" in result:
                    df_hist.at[i, "Печалба/Загуба"] = round(stake * (odd - 1), 2)
                elif "губи" in result:
                    df_hist.at[i, "Печалба/Загуба"] = -stake
                else:
                    df_hist.at[i, "Печалба/Загуба"] = ""
            except:
                df_hist.at[i, "Печалба/Загуба"] = ""

        st.dataframe(df_hist)

        # Метрики
        try:
            valid = df_hist[pd.to_numeric(df_hist["Печалба/Загуба"], errors='coerce').notnull()]
            total_bets = len(valid)
            won = sum(valid["Печалба/Загуба"] > 0)
            lost = sum(valid["Печалба/Загуба"] < 0)
            profit = valid["Печалба/Загуба"].sum()
            total_staked = valid["Сума на залог"].sum()
            roi = (profit / total_staked) * 100 if total_staked > 0 else 0
            success_rate = (won / total_bets) * 100 if total_bets > 0 else 0

            st.markdown("### Статистика:")
            st.metric("Обща печалба", f"{profit:.2f} лв")
            st.metric("ROI", f"{roi:.2f}%")
            st.metric("Успеваемост", f"{success_rate:.2f}%")
        except:
            st.warning("Грешка при изчисление на статистиката.")
