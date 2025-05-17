import requests
import pandas as pd
import streamlit as st

BASE_URL = "https://v3.football.api-sports.io"
API_KEY = st.secrets["API_KEY"]

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}

def get_upcoming_matches(league_ids=[39, 140], count=10):
    """
    Връща предстоящи мачове от избрани лиги.
    league_ids: Списък с ID на лиги (напр. 39 = Premier League, 140 = La Liga)
    count: Колко мача напред да се вземат
    """
    matches = []

    url = f"{BASE_URL}/fixtures?next={count}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.error(f"Грешка при заявка към API: {res.status_code}")
        return pd.DataFrame()

    data = res.json().get("response", [])
    for match in data:
        try:
            team1 = match["teams"]["home"]["name"]
            team2 = match["teams"]["away"]["name"]
            league = match["league"]["name"]
            date = match["fixture"]["date"][:10]
            matches.append({
                "Отбор 1": team1,
                "Отбор 2": team2,
                "Лига": league,
                "Дата": date,
                "Коеф": 2.5  # Задаваме фиктивен коефициент (ще го заменим с реален)
            })
        except Exception as e:
            continue

    return pd.DataFrame(matches)
