import requests
import pandas as pd
from datetime import date

API_KEY = "твоят_ключ_тук"  # замени с реален ключ
API_URL = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

headers = {
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
    "x-rapidapi-key": API_KEY,
}

def load_matches_from_api(selected_date: date) -> pd.DataFrame:
    params = {"date": selected_date.strftime("%Y-%m-%d")}
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        matches = []
        for fixture in data["response"]:
            match = fixture["fixture"]
            league = fixture["league"]["name"]
            teams = fixture["teams"]
            odds = fixture.get("odds", [])

            # Ако няма коефициенти, пропускаме
            if not odds or not odds[0].get("bookmakers"):
                continue

            # Взимаме коефициент за 1X2 от първия букмейкър
            bookmakers = odds[0]["bookmakers"]
            if not bookmakers:
                continue
            markets = bookmakers[0].get("markets", [])
            if not markets:
                continue
            # Търсим 1X2 пазар
            market_1x2 = next((m for m in markets if m["key"] == "h2h"), None)
            if not market_1x2:
                continue
            outcomes = market_1x2.get("outcomes", [])
            # Коефициент за домакин (home team win)
            home_odds = next((o["price"] for o in outcomes if o["name"] == teams["home"]["name"]), None)
            if home_odds is None:
                continue

            matches.append({
                "Отбор 1": teams["home"]["name"],
                "Отбор 2": teams["away"]["name"],
                "Лига": league,
                "Коеф": home_odds,
                "Дата": pd.to_datetime(match["date"]).date()
            })

        df = pd.DataFrame(matches)
        return df[df["Дата"] == selected_date]
    except Exception as e:
        print(f"Грешка при зареждане от API: {e}")
        return pd.DataFrame()
