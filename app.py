import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import requests
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="Value Bets с ML и Реални Мачове", layout="wide")

API_KEY = st.secrets.get("api_football_key", "")

@st.cache_data(ttl=3600)
def fetch_upcoming_matches(league_id=39, season=2025, date=None):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    params = {"league": league_id, "season": season}
    if date:
        params["date"] = date

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        st.error(f"Грешка при заявка към API: {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    matches = []
    if data.get('results', 0) > 0:
        for fixture in data['response']:
            matches.append({
                'Дата': fixture['fixture']['date'][:10],
                'Отбор 1': fixture['teams']['home']['name'],
                'Отбор 2': fixture['teams']['away']['name'],
                'Лига': fixture['league']['name'],
                'Стадион': fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else 'Неизвестен',
            })
    else:
        st.warning("Няма налични мачове за избраната лига и дата.")
    return pd.DataFrame(matches)


def train_model(df):
    features = df[['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A']]
    target = df['FTR']

    le = LabelEncoder()
    target_encoded = le.fit_transform(target)

    X_train, X_test, y_train, y_test = train_test_split(features, target_encoded, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    acc = model.score(X_test, y_test)

    joblib.dump(model, 'value_bet_model.pkl')
    joblib.dump(le, 'label_encoder.pkl')
    return acc


def load_model():
    if os.path.exists('value_bet_model.pkl') and os.path.exists('label_encoder.pkl'):
        model = joblib.load('value_bet_model.pkl')
        le = joblib.load('label_encoder.pkl')
        return model, le
    return None, None


def generate_ml_bets(model, le, n=40):
    leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']
    markets = ['1X2']  # ограничаваме пазара само до 1X2 заради модела
    teams = ['Team A', 'Team B', 'Team C', 'Team D']
    rows = []
    for _ in range(n):
        team1, team2 = random.sample(teams, 2)
        match_time = datetime.now() + timedelta(hours=random.randint(1, 72))
        market = random.choice(markets)
        pick = random.choice(['1', 'X', '2'])

        odds = round(random.uniform(1.5, 3.5), 2)
        fthg = random.randint(0, 4)
        ftag = random.randint(0, 4)
        b365h = round(random.uniform(1.2, 3.0), 2)
        b365d = round(random.uniform(2.5, 4.0), 2)
        b365a = round(random.uniform(1.5, 4.0), 2)

        features = np.array([[fthg, ftag, b365h, b365d, b365a]])
        if model and le:
            pred_probs = model.predict_proba(features)[0]
            pick_map = {'1': 0, 'X': 1, '2': 2}
            est_prob = pred_probs[pick_map[pick]]
        else:
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
            'Импл. %': round(implied_prob * 100, 1),
            'Модел %': round(est_prob * 100, 1),
            'Value %': value
        })

    df = pd.DataFrame(rows)
    return df[df['Value %'] > 0].sort_values(by='Value %', ascending=False).reset_index(drop=True)


st.title("Value Bets с Машинно Обучение и Реални Мачове")

uploaded_files = st.file_uploader("Качи един или повече CSV файла с футболни данни", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            if all(col in df.columns for col in ['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A', 'FTR']):
                all_dfs.append(df)
            else:
                st.warning(f"Файлът {file.name} няма нужните колони и ще бъде пропуснат.")
        except Exception as e:
            st.error(f"Грешка при зареждане на {file.name}: {e}")

    if all_dfs:
        full_df = pd.concat(all_dfs, ignore_index=True)
        st.success(f"Успешно заредени {len(all_dfs)} файла с общо {len(full_df)} записа.")
        st.dataframe(full_df.head())

        if st.button("Обучи модел с всички данни"):
            with st.spinner("Обучение на модела..."):
                acc = train_model(full_df)
                st.success(f"Моделът е обучен успешно! Точност: {acc:.2f}")

model, le = load_model()
if model is None or le is None:
    st.warning("Моделът не е зареден. Качи и обучи нови данни.")

col1, col2 = st.columns(2)
with col1:
    min_value = st.slider("Минимален Value %", 0.0, 20.0, 4.0, step=0.5)
with col2:
    max_rows = st.slider("Макс. брой прогнози", 5, 50, 15)

bets_df = generate_ml_bets(model, le, n=40)
filtered_df = bets_df[bets_df['Value %'] >= min_value].head(max_rows)

st.subheader("Препоръчани залози")
st.dataframe(filtered_df, use_container_width=True)

if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame()

if st.button("Добави всички към история"):
    st.session_state.history = pd.concat([st.session_state.history, filtered_df]).drop_duplicates()

if not st.session_state.history.empty:
    st.subheader("История на залозите")
    st.dataframe(st.session_state.history.reset_index(drop=True), use_container_width=True)

st.header("Реални предстоящи мачове от API-Football")

league = st.selectbox("Избери лига",
                     options=[39, 140, 135, 78],  # Примерни id-та за лиги: Англия, Испания, Италия, Германия
                     format_func=lambda x: {39: "Англия (PL)", 140: "Испания (La Liga)", 135: "Италия (Serie A)", 78: "Германия (Bundesliga)"}[x])

season = st.selectbox("Сезон", options=[2023, 2024, 2025], index=2)

date_filter = st.date_input("Дата (остави празно за всички)", value=None)

date_str = date_filter.strftime("%Y-%m-%d") if date_filter else None

matches_df = fetch_upcoming_matches(league, season, date_str)

st.dataframe(matches_df, use_container_width=True)
