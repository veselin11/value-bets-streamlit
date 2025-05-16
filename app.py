import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import joblib

# Настройки на страницата
st.set_page_config(page_title="Value Bets", layout="wide")

# Зареждане на ML модел и енкодери
model = joblib.load("value_bet_model.pkl")
label_encoders = joblib.load("label_encoders.pkl")

# Функция за ML прогноза
def predict_success_probability(row):
    temp = row.copy()
    for col in ['Лига', 'Пазар', 'Залог']:
        le = label_encoders[col]
        temp[col] = le.transform([temp[col]])[0] if temp[col] in le.classes_ else 0
    X = pd.DataFrame([{
        'League': temp['Лига'],
        'Market': temp['Пазар'],
        'Pick': temp['Залог'],
        'Odds': temp['Коеф.'],
        'ShotsOnTargetDiff': temp['Удари'],
        'PossessionDiff': temp['Притежание'],
        'Value %': temp['Value %']
    }])
    return round(model.predict_proba(X)[0][1] * 100, 1)

# Генериране на прогнози
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
        est_prob = random.uniform(0.35, 0.75)
        implied_prob = 1 / odds
        value = round((est_prob - implied_prob) * 100, 2)
        shots = random.randint(-10, 10)
        possession = random.randint(-50, 50)

        row = {
            'Мач': f'{team1} - {team2}',
            'Час': match_time.strftime('%Y-%m-%d %H:%M'),
            'Лига': league,
            'Пазар': market,
            'Залог': pick,
            'Коеф.': odds,
            'Шанс (%)': round(est_prob * 100, 1),
            'Value %': value,
            'Удари': shots,
            'Притежание': possession
        }
        row['ML Прогноза (%)'] = predict_success_probability(row)
        rows.append(row)

    df = pd.DataFrame(rows)
    return df[df['Value %'] > 0].sort_values(by='Value %', ascending=False).reset_index(drop=True)

# Стил за мобилни устройства
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        .dataframe th, .dataframe td {
            padding: 6px;
            font-size: 14px;
        }
        @media (max-width: 768px) {
            .dataframe th, .dataframe td {
                font-size: 12px;
                padding: 4px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Заглавие
st.title("Value Bets Прогнози с AI")
st.markdown("Прогнози, базирани на value логика и машинно обучение.")

# Настройки
col1, col2 = st.columns(2)
with col1:
    min_value = st.slider("Минимален Value %", 0.0, 20.0, 4.0, step=0.5)
with col2:
    max_rows = st.slider("Макс. брой прогнози", 5, 50, 15)

# Данни
bets_df = generate_value_bets(n=40)
filtered_df = bets_df[bets_df['Value %'] >= min_value].head(max_rows)

# Показване
st.subheader("Препоръчани залози")
st.dataframe(filtered_df, use_container_width=True)

# История
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame()

if st.button("Добави всички към история"):
    st.session_state.history = pd.concat([st.session_state.history, filtered_df]).drop_duplicates()

if not st.session_state.history.empty:
    st.subheader("История на залозите")
    st.dataframe(st.session_state.history.reset_index(drop=True), use_container_width=True)
