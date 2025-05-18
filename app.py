import streamlit as st
import requests

st.set_page_config(page_title="Стойностни залози", layout="centered")

API_KEY = "4474e2c1f44b1561daf6c481deb050cb"
SPORT_KEYS = [
    "soccer_brazil_campeonato",
    "soccer_sweden_allsvenskan",
    "soccer_usa_mls"
]
REGION = "eu"
MARKET = "h2h"
ODDS_FORMAT = "decimal"

st.title("Стойностни залози за днес")

all_matches = []

for sport_key in SPORT_KEYS:
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "markets": MARKET,
        "oddsFormat": ODDS_FORMAT
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        matches = response.json()

        for match in matches:
            home = match.get("home_team")
            away = match.get("away_team")
            commence = match.get("commence_time", "")[:16].replace("T", " ")

            odds = match.get("bookmakers", [])
            if odds:
                h2h = odds[0]["markets"][0]["outcomes"]
                match_data = {
                    "Дата и час": commence,
                    "Домакин": home,
                    "Гост": away,
                    "Коефициенти": {o["name"]: o["price"] for o in h2h}
                }
                all_matches.append(match_data)
    except Exception as e:
        st.error(f"Грешка при зареждане от {sport_key}: {str(e)}")

if all_matches:
    for m in all_matches:
        st.subheader(f'{m["Домакин"]} vs {m["Гост"]}')
        st.write(f'Дата и час: {m["Дата и час"]}')
        for team, odd in m["Коефициенти"].items():
            st.write(f'{team}: {odd}')
        st.markdown("---")
else:
    st.info("Няма стойностни мачове в избраните лиги днес.")
