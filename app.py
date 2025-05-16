import streamlit as st
from datetime import datetime
import pandas as pd

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

tabs = st.tabs(["Прогнози", "История", "Настройки"])

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
                st.session_state["history"].append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Сума": suggested_bet,
                    "Печалба": 0.0,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success(f"Заложено {suggested_bet} лв на {row['Мач']} – {row['Пазар']}")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залозите")

    if st.session_state["history"]:
        for i, bet in enumerate(st.session_state["history"]):
            container_color = "#f0fff0" if bet["Статус"] == "Печели" else "#fff0f0" if bet["Статус"] == "Губи" else "#f9f9f9"
            with st.container():
                st.markdown(f"<div style='background-color:{container_color}; padding:10px; border-radius:10px'>", unsafe_allow_html=True)
                col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.5, 1.2, 1.2, 1.5, 1.5, 2])
                col1.markdown(f"**{bet['Мач']}**")
                col2.write(bet["Пазар"])
                col3.write(f"{bet['Коефициент']:.2f}")
                col4.write(f"{bet['Сума']} лв")
                col5.write(f"{bet['Печалба']:.2f} лв")
                col6.write(bet["Статус"])

                if bet["Статус"] == "Предстои":
                    if col7.button("Печели", key=f"win_{i}"):
                        bet["Статус"] = "Печели"
                        bet["Печалба"] = round(bet["Сума"] * (bet["Коефициент"] - 1), 2)
                        st.experimental_rerun()
                    elif col7.button("Губи", key=f"lose_{i}"):
                        bet["Статус"] = "Губи"
                        bet["Печалба"] = -bet["Сума"]
                        st.experimental_rerun()

                st.markdown("</div>", unsafe_allow_html=True)

        df = pd.DataFrame(st.session_state["history"])
        total_bets = len(df)
        total_staked = df["Сума"].sum()
        total_profit = df["Печалба"].sum()
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        st.markdown("---")
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
        st.success("Новата банка е записана.")
