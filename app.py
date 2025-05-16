import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import requests
import time

st.set_page_config(page_title="Value Bets: ML + Реални мачове", layout="wide")

# ---------------------------
# --- Глобални настройки ---
# ---------------------------
API_KEY = 'ТУК_ВЪВЕДИ_СВОЯ_API_КЛЮЧ'
LEAGUE_ID = 39  # Premier League примерно
SEASON = 2025

# ---------------------------
# --- Функции за ML модел ---
# ---------------------------
def train_model(df):
    # Проверяваме дали имаме нужните колони
    needed_cols = ['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A', 'FTR']
    if not all(col in df.columns for col in needed_cols):
        st.error("Липсват необходими колони за обучение.")
        return None

    features = df[['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A']]
    target = df['FTR']  # 'H','D','A'

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

# ---------------------------
# --- Генериране ML залози ---
# ---------------------------
def generate_ml_bets(model, le, n=40):
    leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']
    markets = ['1X2', 'Over/Under 2.5', 'Both Teams to Score']
    teams = ['Team A', 'Team B', 'Team C', 'Team D']
    rows = []
    for _ in range(n):
        team1, team2 = random.sample(teams, 2)
        match_time = datetime.now() + timedelta(hours=random.randint(1, 72))
        market = random.choice(markets)
        pick = random.choice(['1', 'X', '2', 'Over 2.5', 'Under 2.5', 'Yes', 'No'])

        odds = round(random.uniform(1.5, 3.5), 2)
        fthg = random.randint(0, 4)
        ftag = random.randint(0, 4)
        b365h = round(random.uniform(1.2, 3.0), 2)
        b365d = round(random.uniform(2.5, 4.0), 2)
        b365a = round(random.uniform(1.5, 4.0), 2)

        features = np.array([[fthg, ftag, b365h, b365d, b365a]])

        if model and le:
            pred_probs = model.predict_proba(features)[0]
            pick_map = {'1':0, 'X':1, '2':2}
            if pick in pick_map:
                est_prob = pred_probs[pick_map[pick]]
            else:
                est_prob = random.uniform(0.35, 0.75)
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
            'Шанс (%)': round(est_prob * 100, 1),
            'Value %': value
        })

    df = pd.DataFrame(rows)
    return df[df['Value %'] > 0].sort_values(by='Value %', ascending=False).reset_index(drop=True)

# ---------------------------
# --- Зареждане реални мачове с retry и обработка ---
# ---------------------------
def fetch_upcoming_matches(league_id=LEAGUE_ID, season=SEASON, date=None, max_retries=3, retry_delay=5):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    params = {
        "league": league_id,
        "season": season,
    }
    if date:
        params["date"] = date

    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
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
                return pd.DataFrame(matches)
            else:
                st.warning("Няма налични мачове за избраната лига и дата.")
                return pd.DataFrame()

        elif response.status_code == 403:
            st.error(f"Грешка 403: Достъп отказан (опит {attempt + 1} от {max_retries}). Изчаквам {retry_delay} секунди.")
            time.sleep(retry_delay)
            continue
        else:
            st.error(f"Грешка при заявка: {response.status_code} - {response.text}")
            return pd.DataFrame()

    st.error("Неуспешно зареждане на мачове след няколко опита. Моля, опитайте по-късно.")
    return pd.DataFrame()

# ---------------------------
# --- UI и логика ---
# ---------------------------

st.title("Value Bets - Машинно обучение + Реални мачове")

# --- Качване на файлове за обучение ---
uploaded_files = st.file_uploader("Качи CSV файлове с данни за обучение", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    all_dfs = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            needed_cols = ['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A', 'FTR']
            if all(col in df.columns for col in needed_cols):
                all_dfs.append(df)
            else:
                st.warning(f"Файлът {file.name} няма всички нужни колони и се пропуска.")
        except Exception as e:
            st.error(f"Грешка при зареждане на {file.name}: {e}")

    if all_dfs:
        full_df = pd.concat(all_dfs, ignore_index=True)
        st.success(f"Успешно заредени {len(all_dfs)} файла с общо {len(full_df)} записа.")
        st.dataframe(full_df.head())

        if st.button("Обучи ML модел"):
            with st.spinner("Обучение на модела..."):
                acc = train_model(full_df)
                if acc:
                    st.success(f"Моделът е обучен! Точност на теста: {acc:.2f}")
                else:
                    st.error("Обучението неуспешно.")

model, le = load_model()
if model is None or le is None:
    st.warning("Няма зареден ML модел. Можеш да качиш данни и да го обучиш.")

# --- Генериране ML залози ---
min_value = st.slider("Минимален Value % за прогнози", 0.0, 20.0, 4.0, 0.5)
max_rows = st.slider("Максимален брой прогнози за показване", 5, 50, 15)

bets_df = generate_ml_bets(model, le, n=40)
filtered_df = bets_df[bets_df['Value %'] >= min_value].head(max_rows)

st.subheader("ML Препоръчани Залози")
st.dataframe(filtered_df, use_container_width=True)

# --- История на залозите ---
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame()

if st.button("Добави показаните залози в историята"):
    st.session_state.history = pd.concat([st.session_state.history, filtered_df]).drop_duplicates().reset_index(drop=True)
    st.success(f"Добавени {len(filtered_df)} залози в историята.")

if not st.session_state.history.empty:
    st.subheader("История на залозите")
    st.dataframe(st.session_state.history, use_container_width=True)

# --- Зареждане и показване на реални предстоящи мачове ---
st.header("Реални предстоящи мачове")
date_filter = st.date_input("Избери дата за мачове", value=datetime.today())

if st.button("Зареди мачове от API"):
    with st.spinner("Зареждане..."):
        matches_df = fetch_upcoming_matches(date=date_filter.strftime('%Y-%m-%d'))
        if not matches_df.empty:
            st.dataframe(matches_df)
        else:
            st.info("Няма мачове за избраната дата.")

# --- Статистика (успеваемост, ROI) от историята ---
if not st.session_state.history.empty:
    st.header("Статистика")
    history = st.session_state.history

    # Успеваемост - примерна (ще трябва да се въвеждат резултати ръчно или по API)
    # За момента примерна успеваемост - случайно
    wins = random.randint(0, len(history))
    total = len(history)
    roi = (wins * 0.8 - (total - wins)) / total * 100  # примерен ROI %

    st.metric("Общо залози", total)
    st.metric("Печеливши залози (примерно)", wins)
    st.metric("ROI (примерно)", f"{roi:.2f} %")

st.markdown("---")
st.caption("Версия: 1.0, Обединена версия с всички подобрения.")

