import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import requests

# ------------------- DB -------------------
conn = sqlite3.connect("bets.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        match TEXT,
        market TEXT,
        odds REAL,
        stake REAL,
        status TEXT,
        profit REAL
    )
''')
conn.commit()

# ------------------- FUNCTIONS -------------------
def add_bet(date, match, market, odds, stake, status):
    if status == "win":
        profit = (odds - 1) * stake
    elif status == "lose":
        profit = -stake
    else:
        profit = 0
    c.execute("INSERT INTO bets (date, match, market, odds, stake, status, profit) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (date, match, market, odds, stake, status, profit))
    conn.commit()

def get_all_bets():
    df = pd.read_sql_query("SELECT * FROM bets ORDER BY date DESC", conn)
    return df

def calculate_kpis(df):
    total_stake = df["stake"].sum()
    total_profit = df["profit"].sum()
    roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
    win_rate = len(df[df["status"] == "win"]) / len(df) * 100 if len(df) > 0 else 0
    avg_profit = df["profit"].mean() if len(df) > 0 else 0
    return round(total_profit, 2), round(roi, 2), round(win_rate, 2), round(avg_profit, 2)

# ------------------- ODDS API -------------------
def get_odds_data(region="eu", market="h2h", league="soccer_epl"):
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
    params = {
        "apiKey": st.secrets["ODDS_API_KEY"],
        "regions": region,
        "markets": market,
        "oddsFormat": "decimal"
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.error("Неуспешно извличане на коефициенти.")
        return []

    return response.json()

# ------------------- UI -------------------
st.title("⚽ Спортни залози: Тракер + Value Bet + Live коефициенти")

# Добавяне на залог
with st.form("add_bet"):
    st.subheader("➕ Добави нов залог")
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Дата", value=datetime.today())
        match = st.text_input("Мач", placeholder="Пример: Man City vs Arsenal")
        market = st.selectbox("Пазар", ["1X2", "Over/Under", "Both teams to score", "Друг"])
    with col2:
        odds = st.number_input("Коефициент", min_value=1.01, step=0.01)
        stake = st.number_input("Заложена сума", min_value=0.1, step=0.1)
        status = st.selectbox("Статус", ["win", "lose", "push"])

    submitted = st.form_submit_button("Запази залога")
    if submitted:
        add_bet(str(date), match, market, odds, stake, status)
        st.success("✅ Залогът е запазен успешно!")

# История и анализ
st.divider()
st.subheader("📋 История на залозите")
bets_df = get_all_bets()

if not bets_df.empty:
    st.dataframe(bets_df, use_container_width=True)

    st.subheader("📊 Анализ на представянето")
    profit, roi, winrate, avg_profit = calculate_kpis(bets_df)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Обща печалба", f"{profit:.2f} лв")
    col2.metric("ROI", f"{roi:.2f}%")
    col3.metric("Успеваемост", f"{winrate:.2f}%")
    col4.metric("Средна печалба на залог", f"{avg_profit:.2f} лв")
else:
    st.info("Все още няма въведени залози.")

# Value Bet калкулатор
st.divider()
st.subheader("🎯 Value Bet Калкулатор")

with st.form("value_bet_form"):
    col1, col2 = st.columns(2)
    with col1:
        vb_match = st.text_input("Мач", key="vb_match")
        vb_odds = st.number_input("Коефициент от букмейкър", min_value=1.01, step=0.01, key="vb_odds")
    with col2:
        vb_probability = st.number_input("Твоя вероятност (%)", min_value=1.0, max_value=100.0, step=0.1, key="vb_prob")

    vb_submit = st.form_submit_button("Провери за стойност")

    if vb_submit:
        value = (vb_probability / 100) * vb_odds - 1
        value_percent = value * 100
        if value > 0:
            st.success(f"✅ Има стойност! Value = {value_percent:.2f}%")
        else:
            st.error(f"❌ Няма стойност. Value = {value_percent:.2f}%")

# Live коефициенти от ODDS API
st.divider()
st.subheader("📡 Футболни коефициенти (Premier League)")

odds_data = get_odds_data(league="soccer_epl")

if odds_data:
    for game in odds_data[:5]:
        home = game["home_team"]
        away = game["away_team"]
        commence = game["commence_time"].replace("T", " ").replace("Z", "")
        st.markdown(f"### {home} vs {away} — 🕒 {commence}")

        for bookmaker in game["bookmakers"][:1]:
            st.markdown(f"**📌 Букмейкър:** {bookmaker['title']}")
            for market in bookmaker["markets"]:
                if market["key"] == "h2h":
                    outcomes = market["outcomes"]
                    for o in outcomes:
                        team = o["name"]
                        odds = o["price"]
                        st.write(f"{team}: {odds:.2f}")

            with st.expander("🎯 Провери стойност"):
                selected_team = st.selectbox("Избери отбор", [o["name"] for o in market["outcomes"]], key=game["id"])
                your_prob = st.number_input("Твоя вероятност (%)", min_value=1.0, max_value=100.0, step=0.1, key="vb_" + game["id"])
                if st.button("Провери", key="btn_" + game["id"]):
                    for o in market["outcomes"]:
                        if o["name"] == selected_team:
                            value = (your_prob / 100) * o["price"] - 1
                            value_percent = value * 100
                            if value > 0:
                                st.success(f"✅ Value Bet: {value_percent:.2f}%")
                            else:
                                st.warning(f"❌ Няма стойност: {value_percent:.2f}%")
