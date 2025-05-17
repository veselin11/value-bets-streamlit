import streamlit as st
import requests
from datetime import datetime
import pandas as pd

API_TOKEN = "YOUR_FOOTBALL_DATA_API_TOKEN"  # Тук сложи твоя football-data.org ключ
ODDS_API_TOKEN = "34fd7e0b821f644609d4fac44e3bc30f228e8dc0040b9f0c79aeef702c0f267f"  # Твоят OddsAPI ключ

FOOTBALL_API_URL = "https://api.football-data.org/v4"
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

headers_football = {"X-Auth-Token": API_TOKEN}
params_odds = {
    "apiKey": ODDS_API_TOKEN,
    "regions": "eu",
    "markets": "h2h",  # 1X2 залози
    "oddsFormat": "decimal",
    "dateFormat": "iso"
}

st.title("Value Bets с Реални Коефициенти")

if st.button("Зареди мачове с коефициенти за днес"):
    today = datetime.today().strftime('%Y-%m-%d')

    # Зареждаме мачовете от football-data.org
    response = requests.get(
        f"{FOOTBALL_API_URL}/matches?dateFrom={today}&dateTo={today}", headers=headers_football
    )
    if response.status_code != 200:
        st.error(f"Грешка при зареждане на мачове: {response.status_code}")
        st.stop()

    matches = response.json().get("matches", [])

    # Зареждаме коефициенти от OddsAPI
    odds_response = requests.get(ODDS_API_URL, params=params_odds)
    if odds_response.status_code != 200:
        st.warning("Неуспешно зареждане на коефициенти, ще покажем без тях.")
        odds_data = []
    else:
        odds_data = odds_response.json()

    rows = []
    for match in matches:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        status = match["status"]

        coef_1 = coef_x = coef_2 = None
        for odd in odds_data:
            if odd["home_team"] == home and odd["away_team"] == away:
                for bookmaker in odd["bookmakers"]:
                    for market in bookmaker["markets"]:
                        if market["key"] == "h2h":
                            coef_1 = market["outcomes"][0]["price"]
                            coef_x = market["outcomes"][1]["price"]
                            coef_2 = market["outcomes"][2]["price"]
                            break
                    if coef_1 is not None:
                        break
            if coef_1 is not None:
                break

        rows.append({
            "Час": match["utcDate"][11:16],
            "Домакин": home,
            "Гост": away,
            "Статус": status,
            "Коеф. 1": coef_1 if coef_1 else "-",
            "Коеф. X": coef_x if coef_x else "-",
            "Коеф. 2": coef_2 if coef_2 else "-",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df)
