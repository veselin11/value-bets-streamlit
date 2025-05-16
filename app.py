import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# API настройки
API_KEY = "ee1ece21c66842fd34b7a13f3e6d2730"
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

# Функция за зареждане на наличните лиги
def get_leagues():
    url = f"{BASE_URL}/leagues"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    leagues = data.get("response", [])
    options = [
        {"name": f'{l["league"]["name"]} ({l["country"]["name"]})', "id": l["league"]["id"], "season": l["seasons"][-1]["year"]}
        for l in leagues if l["league"]["type"] == "League"
    ]
    return options

# Функция за зареждане на предстоящи мачове
def get_fixtures(league_id, season, date_str):
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": season,
        "date": date_str
    }
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    fixtures = data.get("response", [])
    matches = []
    for f in fixtures:
        matches.append({
            "Дата": f["fixture"]["date"][:10],
            "Час": f["fixture"]["date"][11:16],
            "Домакин": f["teams"]["home"]["name"],
            "Гост": f["teams"]["away"]["name"],
            "Стадион": f["fixture"]["venue"]["name"] or "N/A"
        })
    return pd.DataFrame(matches)

# Streamlit интерфейс
st.set_page_config(page_title="Value Bets App", layout="wide")
st.title("📊 Value Bets App – Реални предстоящи мачове")

# Зареждане на лиги
with st.spinner("Зареждане на лиги..."):
    leagues = get_leagues()

league_options = {l["name"]: l for l in leagues}
selected_league_name = st.selectbox("Избери лига", list(league_options.keys()))
selected_league = league_options[selected_league_name]

# Избор на дата
today = datetime.today().date()
selected_date = st.date_input("Избери дата за мачове", today)

# Зареждане на мачове
if st.button("🔍 Зареди мачовете"):
    with st.spinner("Зареждане на мачове..."):
        date_str = selected_date.strftime("%Y-%m-%d")
        matches_df = get_fixtures(selected_league["id"], selected_league["season"], date_str)
        if matches_df.empty:
            st.warning("Няма мачове за избраната дата.")
        else:
            st.success(f"Намерени мачове: {len(matches_df)}")
            st.dataframe(matches_df, use_container_width=True)
