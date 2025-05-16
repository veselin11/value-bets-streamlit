import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Value Bets", layout="wide")

# 🧠 Симулирани прогнози
def generate_value_bets(n=40):
    leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']
    markets = ['1X2', 'Over/Under 2.5', 'Both Teams to Score']
    picks = ['1', 'X', '2', 'Over 2.5', 'Under 2.5', 'Yes', 'No']
    teams = ['Team A', 'Team B', 'Team C', 'Team D']
    rows = []
    for _ in range(n):
        team1, team2 = random.sample(teams, 2)
        match_time = datetime.now() + timedelta(hours=random.randint(1, 72))
        market = random.choice(markets)
        pick = random.choice(picks)
        odds = round(random.uniform(1.5, 3.5), 2)
        est_prob = random.uniform(0.35, 0.75)
        implied_prob = 1 / odds
        value = round((est_prob - implied_prob) * 100, 2)
        rows.append({
            'Мач': f'{team1} - {team2}',
            'Час': match_time.strftime('%Y-%m-%d %H:%M'),
            'Лига': random.choice(leagues),
            'Пазар': market,
            'Залог': pick,
            'Коеф.': odds,
            'Шанс (%)': round(est_prob * 100, 1),
            'Value %': value
        })
    df = pd.DataFrame(rows)
    return df[df['Value %'] > 0].sort_values(by='Value %', ascending=False).reset_index(drop=True)

# 📌 Начален интерфейс
st.title("Value Bets Прогнози")
st.markdown("Фокус върху най-добрите стойностни залози по логика на value %.")

# 🔧 Настройки
with st.sidebar:
    st.header("⚙️ Настройки")
    min_value = st.slider("Минимален Value %", 0.0, 20.0, 4.0, step=0.5)
    max_rows = st.slider("Макс. брой прогнози", 5, 50, 15)
    
    selected_market = st.selectbox("Филтър по пазар", ["Всички", "1X2", "Over/Under 2.5", "Both Teams to Score"])
    min_odds, max_odds = st.slider("Филтър по коефициент", 1.0, 5.0, (1.5, 3.5), 0.1)

    bank = st.number_input("💰 Начална банка", value=500.0, step=50.0)
    stake_pct = st.slider("Залог (% от банката)", 1, 10, 5)

# 📈 Данни
bets_df = generate_value_bets()
if selected_market != "Всички":
    bets_df = bets_df[bets_df["Пазар"] == selected_market]
bets_df = bets_df[(bets_df["Коеф."] >= min_odds) & (bets_df["Коеф."] <= max_odds)]
filtered_df = bets_df[bets_df['Value %'] >= min_value].head(max_rows)

# 💰 Изчисление на потенциална печалба
stake_amount = round(bank * (stake_pct / 100), 2)
filtered_df["Залог (лв)"] = stake_amount
filtered_df["Потенциална печалба"] = round(filtered_df["Коеф."] * stake_amount, 2)

# 📊 Прогнози
st.subheader("Препоръчани залози")
st.dataframe(filtered_df, use_container_width=True)

# 📚 История
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame()

if st.button("📌 Добави всички към история"):
    st.session_state.history = pd.concat([st.session_state.history, filtered_df]).drop_duplicates()

# 🧾 Експорт
if not st.session_state.history.empty:
    st.subheader("📜 История на залозите")
    st.dataframe(st.session_state.history.reset_index(drop=True), use_container_width=True)

    csv = st.session_state.history.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Изтегли история като CSV", csv, file_name="bets_history.csv", mime="text/csv")

    # 📈 Графика на печалбата по дни (симулация)
    st.subheader("📈 Печалба по дни (симулация)")
    history = st.session_state.history.copy()
    history["Дата"] = pd.to_datetime(history["Час"]).dt.date
    history["Печалба"] = history["Потенциална печалба"] - history["Залог (лв)"]
    daily = history.groupby("Дата")["Печалба"].sum().cumsum()
    fig, ax = plt.subplots()
    daily.plot(ax=ax)
    ax.set_title("Натрупана печалба по дни")
    ax.set_ylabel("лв")
    st.pyplot(fig)
