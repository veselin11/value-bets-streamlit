import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Стойностни залози", layout="centered")

# Инициализация
if "history" not in st.session_state:
    st.session_state["history"] = []
if "balance" not in st.session_state:
    st.session_state["balance"] = 500.0

# Примерни прогнози
value_bets = [
    {"Мач": "Барселона - Реал", "Пазар": "1Х", "Коефициент": 2.10, "Value %": 15, "Начален час": "22:00"},
    {"Мач": "Арсенал - Челси", "Пазар": "Над 2.5", "Коефициент": 1.85, "Value %": 12, "Начален час": "21:30"},
    {"Мач": "Байерн - Борусия", "Пазар": "Х2", "Коефициент": 3.25, "Value %": 18, "Начален час": "19:45"},
    {"Мач": "Интер - Милан", "Пазар": "1", "Коефициент": 2.50, "Value %": 22, "Начален час": "20:00"},
]

# Цветова индикация
def get_color(value_percent):
    if value_percent >= 20:
        return "#d4edda"
    elif value_percent >= 15:
        return "#fff3cd"
    else:
        return "#f8d7da"

# Табове
tab1, tab2, tab3 = st.tabs(["Прогнози", "История", "Статистика"])

# === Прогнози ===
with tab1:
    st.header("Стойностни прогнози за днес")

    for i, bet in enumerate(value_bets):
        bg = get_color(bet["Value %"])
        with st.container():
            st.markdown(
                f"""<div style='background-color:{bg}; padding:10px; border-radius:10px; margin-bottom:10px'>
                    <b>{bet['Мач']}</b><br>
                    Пазар: {bet['Пазар']} | Коеф.: {bet['Коефициент']} | Value: {bet['Value %']}% | Час: {bet['Начален час']}
                </div>""",
                unsafe_allow_html=True
            )

            if st.button(f"Заложи {round(st.session_state['balance'] * 0.05, -1)} лв", key=f"bet_{i}"):
                amount = round(st.session_state['balance'] * 0.05, -1)
                profit = round((bet["Коефициент"] - 1) * amount, 2)
                st.session_state["history"].append({
                    "Мач": bet["Мач"],
                    "Пазар": bet["Пазар"],
                    "Коефициент": bet["Коефициент"],
                    "Сума": amount,
                    "Печалба": profit,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success(f"Залог добавен: {bet['Мач']}")
                st.rerun()

# === История ===
with tab2:
    st.header("История на залозите")
    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])
        for i, row in df.iterrows():
            status_color = {
                "Печели": "green",
                "Губи": "red",
                "Предстои": "gray"
            }.get(row["Статус"], "gray")

            with st.expander(f"{row['Мач']} – {row['Статус']}"):
                st.markdown(
                    f"""
                    **Пазар:** {row['Пазар']}  
                    **Коефициент:** {row['Коефициент']}  
                    **Сума:** {row['Сума']} лв  
                    **Очаквана печалба:** {row['Печалба']} лв  
                    **Дата:** {row['Дата']}  
                    """
                )
                new_status = st.selectbox("Статус", ["Предстои", "Печели", "Губи"], index=["Предстои", "Печели", "Губи"].index(row["Статус"]), key=f"status_{i}")
                if new_status != row["Статус"]:
                    st.session_state["history"][i]["Статус"] = new_status
                    st.success("Статус обновен.")
                    st.rerun()
    else:
        st.info("Няма запазени залози.")

# === Статистика ===
with tab3:
    st.header("Обща статистика")
    df = pd.DataFrame(st.session_state["history"])
    if not df.empty:
        total_bets = len(df)
        won = df[df["Статус"] == "Печели"]
        lost = df[df["Статус"] == "Губи"]

        net_profit = won["Печалба"].sum() - lost["Сума"].sum()
        roi = net_profit / df["Сума"].sum() * 100 if df["Сума"].sum() > 0 else 0

        st.metric("Общо залози", total_bets)
        st.metric("Нетна печалба", f"{net_profit:.2f} лв")
        st.metric("ROI", f"{roi:.2f}%")

        df["Дата"] = pd.to_datetime(df["Дата"])
        profit_by_date = df[df["Статус"] == "Печели"].groupby(df["Дата"].dt.date)["Печалба"].sum() - df[df["Статус"] == "Губи"].groupby(df["Дата"].dt.date)["Сума"].sum()
        profit_by_date = profit_by_date.fillna(0).cumsum()
        st.line_chart(profit_by_date)
    else:
        st.info("Няма още данни за статистика.")
