import streamlit as st
import pandas as pd
import random
import joblib
import os
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="Value Bets", layout="wide")
st.title("Value Bets Прогнози")

# --------------------------------------
# Обучение на модел в облака при нужда
# --------------------------------------
if st.button("⚙️ Обучи модел (само при нужда)"):
    st.write("Обучаване на модел...")
    data = []
    markets = ['1X2', 'Over/Under 2.5', 'Both Teams to Score']
    picks = ['1', 'X', '2', 'Over 2.5', 'Under 2.5', 'Yes', 'No']
    leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']
    for i in range(500):
        row = {
            'league': leagues[i % len(leagues)],
            'market': markets[i % len(markets)],
            'pick': picks[i % len(picks)],
            'odds': round(1.5 + (i % 20) * 0.1, 2),
            'est_prob': round(0.35 + (i % 40) * 0.01, 2),
            'won': int(i % 2 == 0)
        }
        data.append(row)
    df = pd.DataFrame(data)

    encoders = {}
    for col in ['league', 'market', 'pick']:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le

    X = df[['league', 'market', 'pick', 'odds', 'est_prob']]
    y = df['won']
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, "value_bet_model.pkl")
    joblib.dump(encoders, "label_encoders.pkl")
    st.success("Моделът е обучен успешно и запазен!")

# --------------------------------------
# Зареждане на модела, ако съществува
# --------------------------------------
model = None
encoders = None
if os.path.exists("value_bet_model.pkl") and os.path.exists("label_encoders.pkl"):
    model = joblib.load("value_bet_model.pkl")
    encoders = joblib.load("label_encoders.pkl")

# --------------------------------------
# Генерация на симулирани стойностни залози
# --------------------------------------
def generate_value_bets(n=20):
    leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']
    markets = ['1X2', 'Over/Under 2.5', 'Both Teams to Score']
    picks = ['1', 'X', '2', 'Over 2.5', 'Under 2.5', 'Yes', 'No']
    teams = ['Team A', 'Team B', 'Team C', 'Team D']
    rows = []
    for _ in range(n):
        team1, team2 = random.sample(teams, 2)
        match_time = datetime.now() + timedelta(hours=random.randint(1, 72))
        league = random.choice(leagues)
        market = random.choice(markets)
        pick = random.choice(picks)
        odds = round(random.uniform(1.5, 3.5), 2)
        est_prob = round(random.uniform(0.35, 0.75), 2)
        implied_prob = 1 / odds
        value = round((est_prob - implied_prob) * 100, 2)

        # Предсказание с ML модел
        model_prob = None
        if model and encoders:
            try:
                input_df = pd.DataFrame([{
                    'league': encoders['league'].transform([league])[0],
                    'market': encoders['market'].transform([market])[0],
                    'pick': encoders['pick'].transform([pick])[0],
                    'odds': odds,
                    'est_prob': est_prob
                }])
                pred = model.predict_proba(input_df)[0][1]
                model_prob = round(pred * 100, 1)
            except:
                model_prob = None

        rows.append({
            'Мач': f'{team1} - {team2}',
            'Час': match_time.strftime('%Y-%m-%d %H:%M'),
            'Лига': league,
            'Пазар': market,
            'Залог': pick,
            'Коеф.': odds,
            'Шанс (%)': round(est_prob * 100, 1),
            'Value %': value,
            'Модел %': model_prob if model_prob is not None else "-"
        })
    df = pd.DataFrame(rows)
    return df[df['Value %'] > 0].sort_values(by='Value %', ascending=False).reset_index(drop=True)

# --------------------------------------
# UI настройки
# --------------------------------------
col1, col2 = st.columns(2)
with col1:
    min_value = st.slider("Минимален Value %", 0.0, 20.0, 4.0, step=0.5)
with col2:
    max_rows = st.slider("Макс. брой прогнози", 5, 50, 15)

# --------------------------------------
# Генериране и показване на прогнозите
# --------------------------------------
bets_df = generate_value_bets(n=50)
filtered_df = bets_df[bets_df['Value %'] >= min_value].head(max_rows)

st.subheader("Препоръчани залози")
st.dataframe(filtered_df, use_container_width=True)

# --------------------------------------
# История
# --------------------------------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame()

if st.button("Добави всички към история"):
    st.session_state.history = pd.concat([st.session_state.history, filtered_df]).drop_duplicates()

if not st.session_state.history.empty:
    st.subheader("История на залозите")
    st.dataframe(st.session_state.history.reset_index(drop=True), use_container_width=True)
