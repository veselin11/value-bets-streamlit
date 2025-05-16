import streamlit as st
import pandas as pd
import requests
import joblib
import datetime
from sklearn.preprocessing import LabelEncoder

# Конфигурация на приложението
st.set_page_config(page_title="🎯 Value Bets Finder", layout="wide")
st.title("🎯 Value Bets Finder")

# Зареждане на модела
@st.cache_resource
def load_model():
    model = joblib.load("value_bet_model.pkl")
    le = joblib.load("label_encoder.pkl")
    return model, le

# Функция за изтегляне на мачове
def fetch_upcoming_matches(date=None):
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    headers = {
        "Accept": "application/json",
        "User-Agent": "ValueBetsApp/1.0",
    }
    params = {
        "apiKey": "ТВОЯ_API_КЛЮЧ",
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    if date:
        params["dateFormat"] = "iso"
        params["date"] = date

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"⚠️ Грешка при заявка: {e}")
        return pd.DataFrame()

    matches = []
    for match in data:
        home = match.get("home_team")
        away = match.get("away_team")
        time = match.get("commence_time")
        for bookmaker in match.get("bookmakers", []):
            if bookmaker["key"] == "bet365":
                for market in bookmaker["markets"]:
                    if market["key"] == "h2h":
                        outcomes = {o["name"]: o["price"] for o in market["outcomes"]}
                        matches.append({
                            "home_team": home,
                            "away_team": away,
                            "commence_time": time,
                            "home_odds": outcomes.get(home),
                            "draw_odds": outcomes.get("Draw"),
                            "away_odds": outcomes.get(away),
                        })
    return pd.DataFrame(matches)

# Калкулация на вероятности
def calculate_probabilities(row):
    try:
        row['home_prob'] = 1 / row['home_odds'] if row['home_odds'] else 0
        row['draw_prob'] = 1 / row['draw_odds'] if row['draw_odds'] else 0
        row['away_prob'] = 1 / row['away_odds'] if row['away_odds'] else 0
        total = row['home_prob'] + row['draw_prob'] + row['away_prob']
        if total > 0:
            row['home_prob'] /= total
            row['draw_prob'] /= total
            row['away_prob'] /= total
    except Exception:
        pass
    return row

# Зареждане на модел
try:
    model, le = load_model()
except Exception as e:
    st.error(f"⚠️ Грешка при зареждане на модел: {e}")
    st.stop()

# Избор на дата
date_filter = st.sidebar.date_input("Избери дата", datetime.date.today())

# Зареждане на мачове
st.info("⏳ Зареждане на мачове...")
matches_df = fetch_upcoming_matches(date_filter.strftime('%Y-%m-%d'))

if matches_df.empty:
    st.warning("❌ Няма мачове за избраната дата.")
    st.stop()

# Изчисляване на вероятности
matches_df = matches_df.apply(calculate_probabilities, axis=1)

# Прогнозиране
features = matches_df[["home_prob", "draw_prob", "away_prob"]]
predictions = model.predict(features)
matches_df["prediction"] = le.inverse_transform(predictions)

# Изчисляване на Value
matches_df["value_bet"] = False
for i, row in matches_df.iterrows():
    prediction = row["prediction"]
    if prediction == "home" and row["home_odds"]:
        matches_df.at[i, "value_bet"] = row["home_prob"] * row["home_odds"] > 1.05
    elif prediction == "draw" and row["draw_odds"]:
        matches_df.at[i, "value_bet"] = row["draw_prob"] * row["draw_odds"] > 1.05
    elif prediction == "away" and row["away_odds"]:
        matches_df.at[i, "value_bet"] = row["away_prob"] * row["away_odds"] > 1.05

# Филтриране на Value залози
value_df = matches_df[matches_df["value_bet"] == True]

st.subheader("📈 Открити Value залози")
if not value_df.empty:
    st.dataframe(value_df[["home_team", "away_team", "commence_time", "home_odds", "draw_odds", "away_odds", "prediction"]])
else:
    st.info("🔍 Няма открити стойностни залози за тази дата.")
