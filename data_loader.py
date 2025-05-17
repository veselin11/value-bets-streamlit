import pandas as pd
import requests
import streamlit as st

API_URL = "https://api.example.com/matches"  # смени с твоя API URL
API_KEY = "685e423d2d9e078e7c5f7f9439e77f7c"

def load_matches_from_api(date):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"date": date.strftime("%Y-%m-%d")}

    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("response"):
            st.warning("Няма мачове за избраната дата. Зареждам симулирани мачове.")
            return load_upcoming_matches()

        matches = []
        for match in data["response"]:
            matches.append({
                "Отбор 1": match["team1_name"],
                "Отбор 2": match["team2_name"],
                "Лига": match["league_name"],
                "Коеф": match["odds_home_win"]
            })
        return pd.DataFrame(matches)
    except Exception as e:
        st.error(f"Грешка при зареждане на мачове: {e}")
        return load_upcoming_matches()

def load_upcoming_matches():
    matches = [
        {"Отбор 1": "Лудогорец", "Отбор 2": "ЦСКА", "Лига": "Първа лига", "Дата": "2025-05-18", "Коеф": 2.4},
        {"Отбор 1": "Арсенал", "Отбор 2": "Ман Сити", "Лига": "Висша лига", "Дата": "2025-05-18", "Коеф": 2.8},
    ]
    return pd.DataFrame(matches)
