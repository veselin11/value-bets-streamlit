import requests
import pandas as pd
import streamlit as st
import os
from datetime import datetime

BASE_URL = "https://v3.football.api-sports.io"
API_KEY = st.secrets.get("API_KEY") or os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("Не е зададен API_KEY в средата на изпълнение!")

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}

def get_upcoming_matches(league_ids=None):
    """
    Връща мачовете за днешния ден от избрани лиги (или всички).
    """
    today = datetime.today().strftime('%Y-%m-%d')
    url = f"{BASE_URL}/fixtures?date={today}"
    res = requests.get(url, headers=headers)

    st.write("📅 Търсим мачове за дата:", today)
    st.write("🔍 Статус код на API заявката:", res.status_code)

    try:
        response_data = res.json()
    except Exception:
        st.error("Грешка при четене на JSON отговора от API-то.")
        return pd.DataFrame()

    st.json(response_data)

    if res.status_code != 200 or "response" not in response_data:
        st.error(f"⚠️ API заявката се провали. Код: {res.status_code}")
        return pd.DataFrame()

    data = response_data["response"]
    if not data:
        st.warning("⚠️ Няма мачове за днес.")
        return pd.DataFrame()

    matches = []
    for match in data:
        try:
            league_id = match["league"]["id"]
            if league_ids and league_id not in league_ids:
                continue

            matches.append({
                "Отбор 1": match["teams"]["home"]["name"],
                "Отбор 2": match["teams"]["away"]["name"],
                "Лига": match["league"]["name"],
                "Дата": match["fixture"]["date"][:10],
                "Коеф": 2.5
            })
        except Exception as e:
            st.warning(f"⚠️ Проблем с мач: {e}")
            continue

    return pd.DataFrame(matches)
