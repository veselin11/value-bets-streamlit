import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

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

# === Цветова индикация ===
def get_confidence_color(value_percent):
    if value_percent >= 20:
        return "#b2f2bb"
    elif value_percent >= 15:
        return "#ffe066"
    else:
        return "#ffa8a8"

# === ТАБОВЕ ===
tabs = st.tabs(["Прогнози", "История", "Статистика"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Днес")
    df = pd.DataFrame(value_bets)

    for i, row in df.iterrows():
        bg_color = get_confidence_color(row["Value %"])
        with st.container():
            st.markdown(
                f"""<div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                <b>{row['Мач']}</b><br>Пазар: {row['Пазар']} | Коеф.: {row['Коефициент']:.2f} | Value: {row['Value %']}% | Час: {row['Начален час']}
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(f"Залог {round(st.session_state['balance'] * 0.05, -1)} лв", key=f"bet_{i}"):
                amount = round(st.session_state["balance"] * 0.05, -1)
                profit = round((row["Коефициент"] - 1) * amount, 2)
                st.session_state["history"].append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Сума": amount,
                    "Печалба": profit,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success(f"Залогът е добавен за {row['Мач']}")
                st.rerun()

# === ТАБ 2: История ===
with tabs[1]:
    st.title("История на залозите")

    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])

        for i, row in df.iterrows():
            status_color = {
                "Печели": "green",
                "Губи": "red",
                "Предстои": "gray"
            }.get(row["Статус"], "black")

            with st.expander(f"{row['Мач']} | {row['Пазар']}"):
                st.markdown(f"""
                    **Коефициент:** {row['Коефициент']}  
                    **Сума:** {row['Сума']} лв  
                    **Очаквана печалба:** {row['Печалба']} лв  
                    **Дата:** {row['Дата']}  
                    **Статус:** <span style='color:{status_color}; font-weight:bold'>{row['Статус']}</span>
                """, unsafe_allow_html=True)

                new_status = st.selectbox("Промени статус", ["Предстои", "Печели", "Губи"], index=["Предстои", "Печели", "Губи"].index(row["Статус"]), key=f"status_{i}")
                if new_status != row["Статус"]:
                    st.session_state["history"][i]["Статус"] = new_status
                    st.rerun()

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

        df["Дата"] = pd.to_datetime(df["Дата"])
        df_sorted = df.sort_values("Дата")
        st.line_chart(df_sorted.groupby("Дата")["Печалба"].sum().cumsum())
    else:
        st.info("Няма налични данни за статистика.")
