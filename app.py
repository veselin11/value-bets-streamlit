import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# === API CONFIG ===
API_KEY = "ТВОЯ_API_КЛЮЧ_ТУК"
API_HOST = "v3.football.api-sports.io"
BASE_URL = f"https://{API_HOST}"

headers = {
    "x-apisports-key": API_KEY,
    "x-rapidapi-host": API_HOST,
}

# === APP CONFIG ===
st.set_page_config(page_title="Value Bets", layout="wide")
st.title("⚽ Value Bets – Live и Предстоящи мачове")

# === ФУНКЦИИ ===

@st.cache_data(ttl=3600)
def fetch_leagues():
    url = f"{BASE_URL}/leagues"
    response = requests.get(url, headers=headers)
    data = response.json()
    leagues = [
        {
            "id": l["league"]["id"],
            "name": f'{l["league"]["name"]} ({l["country"]["name"]})',
            "season": l["seasons"][-1]["year"]
        }
        for l in data["response"]
        if l["league"]["type"] == "League" and l["seasons"][-1]["coverage"]["fixtures"]["events"]
    ]
    return sorted(leagues, key=lambda x: x["name"])

def fetch_fixtures(league_id, season, date):
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": season,
        "date": date
    }
    response = requests.get(url, headers=headers, params=params)
    fixtures = response.json().get("response", [])
    matches = []
    for match in fixtures:
        matches.append({
            "Дата": match["fixture"]["date"][:10],
            "Час": match["fixture"]["date"][11:16],
            "Домакин": match["teams"]["home"]["name"],
            "Гост": match["teams"]["away"]["name"],
            "ID": match["fixture"]["id"]
        })
    return pd.DataFrame(matches)

def fake_prediction_logic(df):
    # Тук ще добавим ML модел по-късно
    df["Прогноза"] = "1"  # фиктивно: домакин печели
    df["Коефициент"] = 2.10  # фиктивен коефициент
    df["Value %"] = round((1/0.45) * 100 - 100, 2)  # примерна стойност
    return df

# === UI: Избор на първенство и дата ===
leagues = fetch_leagues()
league_names = [l["name"] for l in leagues]
selected_league = st.selectbox("Избери първенство:", league_names)
selected_date = st.date_input("Избери дата:", value=datetime.today())

# === Зареждане на мачовете ===
league_obj = next(l for l in leagues if l["name"] == selected_league)
fixtures_df = fetch_fixtures(league_obj["id"], league_obj["season"], selected_date.strftime("%Y-%m-%d"))

if fixtures_df.empty:
    st.warning("Няма налични мачове за избраната дата.")
else:
    fixtures_df = fake_prediction_logic(fixtures_df)
    st.success(f"Намерени {len(fixtures_df)} мача за {selected_date.strftime('%Y-%m-%d')}:")
    st.dataframe(fixtures_df, use_container_width=True)

# === TODO: При желание може да добавим бутон "Залагай", история, ROI и графика ===
