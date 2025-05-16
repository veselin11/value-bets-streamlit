import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
st.set_page_config(page_title="Стойностни залози", layout="wide")

# === Сесийна инициализация ===
if "history" not in st.session_state:
    st.session_state["history"] = []
if "balance" not in st.session_state:
    st.session_state["balance"] = 500.0

# === Примерни прогнози ===
value_bets = [
    {"Мач": "Барселона - Реал", "Пазар": "1Х", "Коефициент": 2.10, "Value %": 15, "Начален час": "22:00"},
    {"Мач": "Арсенал - Челси", "Пазар": "Над 2.5", "Коефициент": 1.85, "Value %": 12, "Начален час": "21:30"},
    {"Мач": "Байерн - Борусия", "Пазар": "Х2", "Коефициент": 3.25, "Value %": 18, "Начален час": "19:45"},
    {"Мач": "Интер - Милан", "Пазар": "1", "Коефициент": 2.50, "Value %": 22, "Начален час": "20:00"},
]

# === Функция за цветова индикация на сигурност ===
def get_confidence_color(value_percent):
    if value_percent >= 20:
        return "#b2f2bb"  # светло зелено
    elif value_percent >= 15:
        return "#ffe066"  # жълто
    else:
        return "#ffa8a8"  # светло червено

# === ТАБОВЕ ===
tabs = st.tabs(["Прогнози", "История", "Статистика"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Днес")
    st.caption("Кликни на бутона за залог, за да го добавиш в историята.")

    df = pd.DataFrame(value_bets)

    for i, row in df.iterrows():
        bg_color = get_confidence_color(row["Value %"])
        with st.container():
            st.markdown(
                f"""<div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                    <b>{row['Мач']}</b> | Пазар: {row['Пазар']} | Коеф.: {row['Коефициент']:.2f} | Value: {row['Value %']}% | Час: {row['Начален час']}
                </div>""",
                unsafe_allow_html=True,
            )

            col1, _ = st.columns([1, 4])
            if col1.button(f"Залог {round(st.session_state['balance'] * 0.05, -1)} лв", key=f"bet_{i}"):
                suggested_bet = round(st.session_state["balance"] * 0.05, -1)
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
                st.success(f"Залогът е добавен за {row['Мач']}")
                st.rerun()

# === ТАБ 2: История ===
with tabs[1]:
    st.title("История на залозите")
    hist_df = pd.DataFrame(st.session_state["history"])

    def status_color(status):
        return {
            "Печели": "#d4edda",
            "Губи": "#f8d7da",
            "Предстои": "#fff3cd"
        }.get(status, "white")

    if not hist_df.empty:
        for i, row in hist_df.iterrows():
            cols = st.columns([2, 2, 1, 1, 1, 1])
            bg = status_color(row["Статус"])
            with cols[0]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Мач']}</div>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Пазар']}</div>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Коефициент']}</div>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Сума']} лв</div>", unsafe_allow_html=True)
            with cols[4]:
                status = st.selectbox("", ["Предстои", "Печели", "Губи"], index=["Предстои", "Печели", "Губи"].index(row["Статус"]), key=f"status_{i}")
                st.session_state["history"][i]["Статус"] = status

    else:
        st.info("Няма още запазени залози.")

# === ТАБ 3: Статистика ===
with tabs[2]:
    st.title("Обща статистика")
    df = pd.DataFrame(st.session_state["history"])
    if not df.empty:
        total_bets = len(df)
        won = df[df["Статус"] == "Печели"]
        lost = df[df["Статус"] == "Губи"]

        net_profit = won["Печалба"].sum() - lost["Сума"].sum()
        roi = net_profit / df["Сума"].sum() * 100 if df["Сума"].sum() > 0 else 0

        st.metric("Залози", total_bets)
        st.metric("Печалба", f"{net_profit:.2f} лв")
        st.metric("ROI", f"{roi:.2f}%")

        st.line_chart(df.groupby("Дата")["Печалба"].sum().cumsum())
    else:
        st.info("Няма налични данни за статистика.")
