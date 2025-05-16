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

# === Цветови индикатор за value ===
def get_confidence_color(value_percent):
    if value_percent >= 20:
        return "#b2f2bb"
    elif value_percent >= 15:
        return "#ffe066"
    else:
        return "#ffa8a8"

# === Tabs ===
tabs = st.tabs(["Прогнози", "История", "Статистика"])

# === TAB 1: Прогнози ===
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
            bet_amount = round(st.session_state['balance'] * 0.05, -1)
            col1, _ = st.columns([1, 4])
            if col1.button(f"Залог {bet_amount} лв", key=f"bet_{i}"):
                profit = round((row["Коефициент"] - 1) * bet_amount, 2)
                st.session_state["history"].append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Сума": bet_amount,
                    "Печалба": profit,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success(f"Залогът е добавен за {row['Мач']}")
                st.rerun()

# === TAB 2: История ===
with tabs[1]:
    st.title("История на залозите")

    df_hist = pd.DataFrame(st.session_state["history"])
    if not df_hist.empty:
        status_filter = st.selectbox("Филтрирай по статус", ["Всички", "Предстои", "Печели", "Губи"])
        if status_filter != "Всички":
            df_hist = df_hist[df_hist["Статус"] == status_filter]

        st.markdown("### Залози")
        for i, row in df_hist.iterrows():
            st.markdown(
                f"""<div style="background-color: #f8f9fa; padding: 10px; border-radius: 10px; margin-bottom: 8px;">
                    <b>{row['Мач']}</b> | Пазар: {row['Пазар']} | Коеф.: {row['Коефициент']} | Сума: {row['Сума']} лв | 
                    Печалба: {row['Печалба']} лв | Статус: <b>{row['Статус']}</b> | <i>{row['Дата']}</i>
                </div>""",
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.info("За да променяш статуси или триеш залози, ще добавим отделен екран при нужда.")
    else:
        st.info("Няма запазени залози.")

# === TAB 3: Статистика ===
with tabs[2]:
    st.title("Обща статистика")

    df = pd.DataFrame(st.session_state["history"])
    if not df.empty:
        total_bets = len(df)
        won = df[df["Статус"] == "Печели"]
        lost = df[df["Статус"] == "Губи"]
        net_profit = won["Печалба"].sum() - lost["Сума"].sum()
        roi = net_profit / df["Сума"].sum() * 100 if df["Сума"].sum() > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Общо залози", total_bets)
        col2.metric("Нетна печалба", f"{net_profit:.2f} лв")
        col3.metric("ROI", f"{roi:.2f}%")

        st.markdown("### Графика на натрупана печалба")
        chart_df = df.copy()
        chart_df["Дата"] = pd.to_datetime(chart_df["Дата"])
        chart_df = chart_df.sort_values("Дата")
        chart_df["Натрупана печалба"] = chart_df.apply(
            lambda row: row["Печалба"] if row["Статус"] == "Печели"
            else -row["Сума"] if row["Статус"] == "Губи" else 0, axis=1
        ).cumsum()

        st.line_chart(chart_df.set_index("Дата")["Натрупана печалба"])
    else:
        st.info("Няма достатъчно данни за статистика.")
