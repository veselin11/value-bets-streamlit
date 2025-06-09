import streamlit as st
import sqlite3
import pandas as pd from datetime
import datetime

------------------- DB -------------------

conn = sqlite3.connect("bets.db", check_same_thread=False) c = conn.cursor()

c.execute(''' CREATE TABLE IF NOT EXISTS bets ( id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, match TEXT, market TEXT, odds REAL, stake REAL, status TEXT, profit REAL ) ''') conn.commit()

------------------- FUNCTIONS -------------------

def add_bet(date, match, market, odds, stake, status): if status == "win": profit = (odds - 1) * stake elif status == "lose": profit = -stake else: profit = 0 c.execute("INSERT INTO bets (date, match, market, odds, stake, status, profit) VALUES (?, ?, ?, ?, ?, ?, ?)", (date, match, market, odds, stake, status, profit)) conn.commit()

def get_all_bets(): df = pd.read_sql_query("SELECT * FROM bets ORDER BY date DESC", conn) return df

def calculate_kpis(df): total_stake = df["stake"].sum() total_profit = df["profit"].sum() roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0 win_rate = len(df[df["status"] == "win"]) / len(df) * 100 if len(df) > 0 else 0 avg_profit = df["profit"].mean() if len(df) > 0 else 0 return round(total_profit, 2), round(roi, 2), round(win_rate, 2), round(avg_profit, 2)

------------------- UI -------------------

st.title("📈 Тракер за спортни залози")

with st.form("add_bet"): st.subheader("➕ Добави нов залог") col1, col2 = st.columns(2) with col1: date = st.date_input("Дата", value=datetime.today()) match = st.text_input("Мач", placeholder="Пример: Man City vs Arsenal") market = st.selectbox("Пазар", ["1X2", "Over/Under", "Both teams to score", "Друг"]) with col2: odds = st.number_input("Коефициент", min_value=1.01, step=0.01) stake = st.number_input("Заложена сума", min_value=0.1, step=0.1) status = st.selectbox("Статус", ["win", "lose", "push"])

submitted = st.form_submit_button("Запази залога")
if submitted:
    add_bet(str(date), match, market, odds, stake, status)
    st.success("✅ Залогът е запазен успешно!")

st.divider() st.subheader("📋 История на залозите")

bets_df = get_all_bets()

if not bets_df.empty: st.dataframe(bets_df, use_container_width=True)

st.subheader("📊 Анализ на представянето")
profit, roi, winrate, avg_profit = calculate_kpis(bets_df)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Обща печалба", f"{profit:.2f} лв")
col2.metric("ROI", f"{roi:.2f}%")
col3.metric("Успеваемост", f"{winrate:.2f}%")
col4.metric("Средна печалба на залог", f"{avg_profit:.2f} лв")

else: st.info("Все още няма въведени залози.")

