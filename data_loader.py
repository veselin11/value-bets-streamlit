import requests
import pandas as pd
from datetime import date

API_KEY = "685e423d2d9e078e7c5f7f9439e77f7c"  # Смени с твоя API ключ

def load_matches_from_api(selected_date: date):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "date": selected_date.strftime("%Y-%m-%d"),
        "timezone": "Europe/Sofia"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        matches = data.get("response", [])
        if not matches:
            return pd.DataFrame()

        rows = []
        for m in matches:
            fixture = m["fixture"]
            league = m["league"]
            teams = m["teams"]

            row = {
                "Отбор 1": teams["home"]["name"],
                "Отбор 2": teams["away"]["name"],
                "Лига": league["name"],
                "Коеф": 2.0,  # Ако нямаш коефициенти, сложи фиксирана стойност или си добави от друг източник
                "Дата": pd.to_datetime(fixture["date"]).date()
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        return df

    except Exception as e:
        print(f"Грешка при зареждане от API: {e}")
        return pd.DataFrame()
