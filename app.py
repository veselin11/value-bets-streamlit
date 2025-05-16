import streamlit as st
from datetime import datetime
import pandas as pd
import altair as alt

st.set_page_config(page_title="Стойностни залози", layout="wide")

# Сесийна инициализация
if "history" not in st.session_state:
    st.session_state["history"] = []

if "balance" not in st.session_state:
    st.session_state["balance"] = 500

# Примерни стойностни мачове
value_bets = [
    {"Мач": "Arsenal vs Chelsea", "Пазар": "1", "Коефициент": 2.2, "Value %": 6.5, "Начален час": "21:00"},
    {"Мач": "Real Madrid vs Barcelona", "Пазар": "ГГ", "Коефициент": 1.9, "Value %": 8.1, "Начален час": "22:00"},
    {"Мач": "Bayern vs Dortmund", "Пазар": "Над 2.5", "Коефициент": 2.05, "Value %": 7.2, "Начален час": "19:30"},
]

tabs = st.tabs(["Прогнози", "История", "Настройки", "Статистика"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Симулирани данни")
    st.caption("Кликни на Сума за залог, за да запишеш мача в историята")

    df = pd.DataFrame(value_bets)

    for i, row in df.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1.5, 1.2, 1.2, 1.2, 2])
            col1.markdown(f"**{row['Мач']}**")
            col2.write(row["Пазар"])
            col3.write(f"{row['Коефициент']:.2f}")
            col4.write(f"{row['Value %']}%")
            col5.write(row["Начален час"])

            suggested_bet = round(st.session_state["balance"] * 0.05, -1)
            if col6.button(f"Залог {suggested_bet} лв", key=f"bet_{i}"):
                profit = round((row["Коефициент"] - 1) * suggested_bet, 2)
                st.session_state["history"].append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Сума": suggested_bet,
                    "Печалба": profit,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success(f"Заложено {suggested_bet} лв на {row['Мач']} – {row['Пазар']}")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залозите")
    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])
        st.dataframe(history_df, use_container_width=True)

        total_bets = len(history_df)
        total_staked = sum(b["Сума"] for b in st.session_state["history"])
        total_profit = sum(b["Печалба"] for b in st.session_state["history"])
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Залози", total_bets)
        col2.metric("Нетна печалба", f"{total_profit:.2f} лв")
        col3.metric("ROI", f"{roi:.2f}%")
    else:
        st.info("Няма още заложени мачове.")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки на системата")
    new_balance = st.number_input("Начална банка", min_value=100, value=st.session_state["balance"], step=10)
    if st.button("Запази"):
        st.session_state["balance"] = new_balance
        st.success("Новата банка е запазена.")

# === ТАБ 4: Статистика ===
with tabs[3]:
    st.header("Статистика")
    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])
        df["Дата"] = pd.to_datetime(df["Дата"])

        # Успеваемост (базирано на положителна печалба)
        wins = df[df["Печалба"] > 0]
        success_rate = len(wins) / len(df) * 100

        # Среден value (ако има такива данни)
        avg_value = df["Коефициент"].mean() if not df.empty else 0

        col1, col2 = st.columns(2)
        col1.metric("Успеваемост", f"{success_rate:.2f}%")
        col2.metric("Среден коефициент", f"{avg_value:.2f}")

        # Печалба по дни
        profit_by_day = df.groupby(df["Дата"].dt.date)["Печалба"].sum().reset_index()
        profit_by_day.columns = ["Дата", "Печалба"]

        chart = alt.Chart(profit_by_day).mark_bar().encode(
            x="Дата:T",
            y="Печалба:Q",
            tooltip=["Дата", "Печалба"]
        ).properties(title="Нетна печалба по дни", height=300)

        st.altair_chart(chart, use_container_width=True)

        # Графика на банката по дни
        profit_by_day = profit_by_day.sort_values("Дата")
        profit_by_day["Банка"] = st.session_state["balance"] + profit_by_day["Печалба"].cumsum()

        balance_chart = alt.Chart(profit_by_day).mark_line(point=True).encode(
            x="Дата:T",
            y=alt.Y("Банка:Q", title="Банка (лв)"),
            tooltip=["Дата", "Банка"]
        ).properties(title="Растеж на банката по дни", height=300)

        st.altair_chart(balance_chart, use_container_width=True)
    else:
        st.info("Няма достатъчно данни за статистика.")
