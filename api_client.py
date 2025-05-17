import os
import streamlit as st
import requests
import pandas as pd

# Зареждане на API ключ от secrets или променливи на средата
API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("Не е зададен API_KEY в Streamlit secrets или променливите на средата!")

BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}

def get_upcoming_matches(league_ids=[39, 140], count=10):
    matches = []
    url = f"{BASE_URL}/fixtures?next={count}"
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        st.error(f"Грешка при заявка към API: {res.status_code}")
        return pd.DataFrame()

    data = res.json().get("response", [])
    for match in data:
        league_id = match["league"]["id"]
        if league_id not in league_ids:
            continue
        try:
            matches.append({
                "Отбор 1": match["teams"]["home"]["name"],
                "Отбор 2": match["teams"]["away"]["name"],
                "Лига": match["league"]["name"],
                "Дата": match["fixture"]["date"][:10],
                "Коеф": 2.5  # фиктивен коефициент, може да го заменим с реален при нужда
            })
        except:
            continue

    return pd.DataFrame(matches)
