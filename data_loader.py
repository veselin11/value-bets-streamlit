import requests
import pandas as pd
from datetime import date

API_KEY = "685e423d2d9e078e7c5f7f9439e77f7c"
API_URL = "https://v3.football.api-sports.io/fixtures"

HEADERS = {
    "x-apisports-key": API_KEY
}

def load_matches_from_api(selected_date: date):
    try:
        params = {
            "date": selected_date.strftime("%Y-%m-%d"),
            "season": "2024",
            # Можеш да добавиш филтри по лиги тук, ако искаш
        }
        response = requests.get(API_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        matches = []
        for fixture in data.get("response", []):
            match = {
                "Отбор 1": fixture["teams"]["home"]["name"],
                "Отбор 2": fixture["teams"]["away"]["name"],
                "Лига": fixture["league"]["name"],
                "Коеф": fixture["bookmakers"][0]["bets"][0]["values"][0]["odd"] if fixture["bookmakers"] else 1.0,
                "Дата": pd.to_datetime(fixture["fixture"]["date"]).date(),
            }
            matches.append(match)

        df = pd.DataFrame(matches)
        return df

    except Exception as e:
        print(f"Грешка при зареждане на мачове от API: {e}")
        return pd.DataFrame()
