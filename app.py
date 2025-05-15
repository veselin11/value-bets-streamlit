import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Стойностни залози", layout="wide")

# Сесийна променлива за история
if "bet_history" not in st.session_state:
    st.session_state.bet_history = []

# Настройки
with st.sidebar:
    st.title("Настройки на банката")
    starting_bankroll = st.number_input("Начална банка (лв)", value=500.0)
    daily_goal_percent = st.number_input("Дневна цел (% от банката)", value=6.0)
    period_days = st.number_input("Период (дни)", value=5)
    if "bankroll" not in st.session_state:
        st.session_state.bankroll = starting_bankroll

# Функция за изчисление на сумата за залог
def calculate_bet_amount(bankroll, goal_percent, days):
    total_target = bankroll * (goal_percent / 100) * days
    daily_target = total_target / days
    return round(daily_target, 2)

bet_amount = calculate_bet_amount(st.session_state.bankroll, daily_goal_percent, period_days)

# Фиктивни стойностни залози
def generate_fake_value_bets():
    teams = ["Арсенал", "Челси", "Манчестър Юн.", "Ливърпул", "Барселона", "Реал М.", "Байерн", "Ювентус"]
    bets = []
    for _ in range(10):
        home, away = random.sample(teams, 2)
        market = random.choice(["1", "X", "2", "Над 2.5", "Под 2.5", "ГГ", "НГ"])
        odds = round(random.uniform(1.7, 3.5), 2)
        fair_prob = random.uniform(0.35, 0.65)
        implied_prob = 1 / odds
        value_pct = round((fair_prob - implied_prob) * 100, 2)
        if value_pct > 0:
            bets.append({
                "Мач": f"{home} - {away}",
                "Пазар": market,
                "Коеф.": odds,
                "Value %": value_pct,
                "Прогноза": market,
                "Дата": datetime.now().strftime("%d.%m.%Y %H:%M")
            })
    return pd.DataFrame(bets)

# Tabs
tab1, tab2, tab3 = st.tabs(["Прогнози", "История", "Статистика"])

# --- Прогнози ---
with tab1:
    st.header("Препоръчани стойностни залози")
    df_bets = generate_fake_value_bets()
    st.dataframe(df_bets, use_container_width=True)

    selected = st.multiselect("Избери залози за добавяне в историята", df_bets["Мач"] + " | " + df_bets["Пазар"])

    if st.button("Добави в историята"):
        for val in selected:
            row = df_bets[df_bets["Мач"] + " | " + df_bets["Пазар"] == val].iloc[0]
            st.session_state.bet_history.append({
                "Дата": row["Дата"],
                "Мач": row["Мач"],
                "Пазар": row["Пазар"],
                "Коеф.": row["Коеф."],
                "Value %": row["Value %"],
                "Залог": bet_amount,
                "Резултат": "?"  # по-късно се попълва
            })
        st.success("Залозите са добавени.")

# --- История ---
with tab2:
    st.header("История на залозите")
    df_hist = pd.DataFrame(st.session_state.bet_history)
    if not df_hist.empty:
        edited = st.data_editor(df_hist, num_rows="dynamic", use_container_width=True, key="editor")
        st.session_state.bet_history = edited.to_dict("records")
    else:
        st.info("Все още няма добавени залози.")

# --- Статистика ---
with tab3:
    st.header("Статистика")
    df_hist = pd.DataFrame(st.session_state.bet_history)
    if not df_hist.empty:
        df = df_hist[df_hist["Резултат"].isin(["Печели", "Губи"])]
        df["Печалба"] = df.apply(lambda x: x["Залог"] * (x["Коеф."] - 1) if x["Резултат"] == "Печели" else -x["Залог"], axis=1)
        total_bets = len(df)
        wins = len(df[df["Печалба"] > 0])
        profit = df["Печалба"].sum()
        roi = profit / (total_bets * bet_amount) * 100 if total_bets > 0 else 0
        avg_value = df_hist["Value %"].mean()

        st.metric("Общо залози", total_bets)
        st.metric("Печалба (лв)", f"{profit:.2f}")
        st.metric("ROI %", f"{roi:.2f}")
        st.metric("Успеваемост", f"{wins / total_bets * 100:.1f}%" if total_bets else "—")
        st.metric("Среден Value %", f"{avg_value:.2f}")
    else:
        st.info("Няма налични данни за статистика.")
