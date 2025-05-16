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
                    "Дата": datetime.now().strftime("%Y-%m-%d"),
                    "Статус": "Предстои"
                })
                st.success(f"Заложено {suggested_bet} лв на {row['Мач']} – {row['Пазар']}")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залозите")

    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])

        status_filter = st.selectbox("Филтрирай по статус", ["Всички", "Предстои", "Печели", "Губи", "Отменен"])
        if status_filter != "Всички":
            history_df = history_df[history_df["Статус"] == status_filter]

        for i, row in history_df.iterrows():
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.2, 1, 1, 1, 1.5, 2])
                col1.markdown(f"**{row['Мач']}**")
                col2.write(row["Пазар"])
                col3.write(f"{row['Коефициент']}")
                col4.write(f"{row['Сума']} лв")
                col5.write(f"{row['Печалба']} лв")
                col6.write(row["Статус"])

                if row["Статус"] == "Предстои":
                    result = col7.selectbox("Обнови", ["-", "Печели", "Губи", "Отменен"], key=f"res_{i}")
                    if result != "-":
                        if result == "Печели":
                            profit = round((row["Коефициент"] - 1) * row["Сума"], 2)
                        elif result == "Губи":
                            profit = -row["Сума"]
                        else:
                            profit = 0.0
                        st.session_state["history"][i]["Статус"] = result
                        st.session_state["history"][i]["Печалба"] = profit
                        st.experimental_rerun()

        # Обобщена статистика
        settled = [b for b in st.session_state["history"] if b["Статус"] in ["Печели", "Губи", "Отменен"]]
        total_bets = len(settled)
        total_staked = sum(b["Сума"] for b in settled)
        total_profit = sum(b["Печалба"] for b in settled)
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Реални залози", total_bets)
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
    st.header("Разширена статистика")

    hist_df = pd.DataFrame(st.session_state["history"])
    hist_df["Дата"] = pd.to_datetime(hist_df["Дата"])

    if not hist_df.empty:
        profit_by_day = hist_df[hist_df["Статус"].isin(["Печели", "Губи", "Отменен"])].groupby("Дата")["Печалба"].sum().reset_index()

        profit_chart = alt.Chart(profit_by_day).mark_bar().encode(
            x="Дата:T",
            y="Печалба:Q",
            tooltip=["Дата", "Печалба"]
        ).properties(title="Нетна печалба по дни", height=300)

        st.altair_chart(profit_chart, use_container_width=True)

        # Успеваемост
        total_settled = hist_df[hist_df["Статус"].isin(["Печели", "Губи"])]
        win_rate = (total_settled["Статус"] == "Печели").mean() * 100 if not total_settled.empty else 0

        st.metric("Успеваемост", f"{win_rate:.1f}%")
    else:
        st.info("Няма достатъчно данни за графики.")
