import os
import streamlit as st

API_KEY = os.getenv("API_KEY") or st.secrets.get("API_KEY")

if not API_KEY:
    raise ValueError("Не е зададен API_KEY в средата или в secrets!")


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
        print(f"Грешка при заявка към API: {res.status_code}")
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
                "Коеф": 2.5  # Фиктивен коефициент за сега
            })
        except Exception:
            continue

    return pd.DataFrame(matches)
