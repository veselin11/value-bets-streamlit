import os
import requests
import pandas as pd
import streamlit as st

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("Не е зададен API_KEY в средата на изпълнение!")

BASE_URL = "https://v3.football.api-sports.io"
headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}

def get_upcoming_matches(date:str):
    """
    Връща предстоящи мачове за конкретна дата.
    date: формат 'YYYY-MM-DD'
    """
    url = f"{BASE_URL}/fixtures?date={date}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.error(f"Грешка при заявка към API: {res.status_code}")
        return pd.DataFrame()
    
    data = res.json()
    matches = []
    for match in data.get("response", []):
        try:
            matches.append({
                "Отбор 1": match["teams"]["home"]["name"],
                "Отбор 2": match["teams"]["away"]["name"],
                "Лига": match["league"]["name"],
                "Дата": match["fixture"]["date"][:10],
                "Коеф": 2.5  # временно фиктивен коефициент
            })
        except:
            continue
    return pd.DataFrame(matches)
