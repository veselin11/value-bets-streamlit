import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_KEY = "34fd7e0b821f644609d4fac44e3bc30f228e8dc0040b9f0c79aeef702c0f267f"

BASE_URL = "https://allsportsapi.com/api/football/"

def get_fixtures_for_today(api_key):
    today = datetime.today().strftime('%Y-%m-%d')
    params = {
        "met": "Fixtures",
        "APIkey": api_key,
        "from": today,
        "to": today,
        "leagueId": "",  # ако искаш, сложи конкретна лига, иначе празно
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        st.error(f"Грешка при зареждане на мачове: {response.status_code}")
        return pd.DataFrame()

    data = response.json()

    # Погледни ключовете на data, ако няма "result" - провери как се връща резултата
    if "result" not in data:
        st.error(f"API отговор без 'result' ключ: {data}")
        return pd.DataFrame()

    matches = data["result"]
    rows = []
    for m in matches:
        rows.append({
            "Час": m.get("match_time", ""),
            "Дата": m.get("event_date", ""),
            "Домакин": m.get("event_home_team", ""),
            "Гост": m.get("event_away_team", ""),
            "Лига": m.get("league_name", ""),
            "Статус": m.get("event_status", ""),
        })
    return pd.DataFrame(rows)

st.title("Value Bets с allsportsapi.com")

if st.button("Зареди мачове за днес"):
    df_matches = get_fixtures_for_today(API_KEY)
    if not df_matches.empty:
        st.dataframe(df_matches)
    else:
        st.info("Няма мачове за днес или проблем с API.")
