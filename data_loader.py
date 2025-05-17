import requests
import pandas as pd
from datetime import date

API_KEY = "685e423d2d9e078e7c5f7f9439e77f7c"  # Тук смени с твоя ключ
API_URL = "https://v3.football.api-sports.io/fixtures"

HEADERS = {
    "x-apisports-key": API_KEY
}

def load_matches_from_api(selected_date: date):
    params = {
        "date": selected_date.isoformat(),
        "season": "2024"
    }

    response = requests.get(API_URL, headers=HEADERS, params=params)
    data = response.json()

    if not data.get("response"):
        return pd.DataFrame()

    rows = []
    for fixture in data["response"]:
        teams = fixture["teams"]
        odds = fixture.get("odds")
        if not odds or not odds[0]["bookmakers"]:
            continue

        bookmaker = odds[0]["bookmakers"][0]
        markets = bookmaker["markets"]
        market = next((m for m in markets if m["key"] == "h2h"), None)
        if not market:
            continue

        outcomes = market["outcomes"]

        home_odd = away_odd = draw_odd = None
        for outcome in outcomes:
            if outcome["name"] == teams["home"]["name"]:
                home_odd = outcome["price"]
            elif outcome["name"] == teams["away"]["name"]:
                away_odd = outcome["price"]
            elif outcome["name"].lower() in ["draw", "равен"]:
                draw_odd = outcome["price"]

        if home_odd is None:
            continue

        rows.append({
            "Отбор 1": teams["home"]["name"],
            "Отбор 2": teams["away"]["name"],
            "Лига": fixture["league"]["name"],
            "Коеф": home_odd,  # Можеш да добавиш още пазари, ако искаш
            "Дата": pd.to_datetime(fixture["fixture"]["date"]).date()
        })

    df = pd.DataFrame(rows)
    return df[df["Дата"] == selected_date]
