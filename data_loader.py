import requests
import pandas as pd
from datetime import date

API_KEY = "тук_сложи_твоят_API_ключ"  # По-добре да е в secrets или env

def load_matches_from_api(selected_date: date):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_KEY
    }
    params = {
        "date": selected_date.strftime("%Y-%m-%d")
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        fixtures = data.get("response", [])
        
        # Преобразуваме JSON в DataFrame с нужните колони:
        rows = []
        for match in fixtures:
            fixture = match["fixture"]
            league = match["league"]
            teams = match["teams"]
            odds = match.get("odds", [])
            # Понякога odds може да са празни, ще използваме фиктивна стойност 2.0
            coef = 2.0
            # Ако има odds, взимаме първия коефициент за домакин победа
            if odds:
                # В зависимост от структурата, примерно:
                bookie = odds[0]  
                if bookie.get("bookmaker") and bookie.get("bets"):
                    bets = bookie["bets"]
                    # Търсим пазара "Match Winner"
                    for bet in bets:
                        if bet.get("name") == "Match Winner":
                            for val in bet.get("values", []):
                                if val.get("value") == "Home":
                                    coef = float(val.get("odd", 2.0))
                                    break

            rows.append({
                "Отбор 1": teams["home"]["name"],
                "Отбор 2": teams["away"]["name"],
                "Лига": league["name"],
                "Коеф": coef,
                "Дата": pd.to_datetime(fixture["date"]).date()
            })
        df = pd.DataFrame(rows)
        return df[df["Дата"] == selected_date]
    except Exception as e:
        print(f"Грешка при зареждане на мачове от API: {e}")
        return pd.DataFrame()
