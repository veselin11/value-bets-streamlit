import streamlit as st
import requests
import datetime
import statistics

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

EUROPE_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_russia_premier_league",
    "soccer_austria_bundesliga",
    "soccer_sweden_allsvenskan",
    "soccer_norway_eliteserien",
    "soccer_denmark_superliga",
    "soccer_league_of_ireland"
]

st.title("Стойностни Залози с Висок Потенциал")

st.write("Зареждам мачове и изчислявам най-добрите стойностни залози...")

value_bets = []

for league_key in EUROPE_LEAGUES:
    url = f"{BASE_URL}/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        if not matches:
            continue

        for match in matches:
            match_time = datetime.datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00"))
            home = match.get("home_team")
            away = match.get("away_team")
            bookmakers = match.get("bookmakers", [])

            for market in [m for b in bookmakers for m in b.get("markets", []) if m["key"] == "h2h"]:
                outcomes = market.get("outcomes", [])
                if not outcomes:
                    continue
                
                odds = [o["price"] for o in outcomes if o.get("price")]
                if len(odds) < 2:
                    continue

                avg_odd = statistics.mean(odds)
                for outcome in outcomes:
                    best_odd = outcome["price"]
                    implied_prob = 1 / avg_odd
                    fair_odd = 1 / implied_prob
                    value = best_odd - fair_odd
                    value_percent = (value / fair_odd) * 100

                    if value_percent > 5:
                        value_bets.append({
                            "match": f"{home} vs {away}",
                            "time": match_time.strftime("%Y-%m-%d %H:%M"),
                            "selection": outcome["name"],
                            "odd": best_odd,
                            "probability": round(implied_prob * 100, 1),
                            "value": round(value_percent, 1),
                            "league": league_key
                        })

    except Exception as e:
        st.warning(f"Проблем с {league_key}: {e}")

if value_bets:
    value_bets.sort(key=lambda x: x["value"], reverse=True)
    st.subheader("ТОП Стойностни Прогнози")
    for bet in value_bets[:10]:
        st.markdown(
            f"**{bet['match']}** ({bet['time']})  \
            Лига: {bet['league']}  \
            Залог: {bet['selection']}  \
            Коефициент: {bet['odd']:.2f}  \
            Вероятност: {bet['probability']}%  \
            Value: +{bet['value']}%"
        )
else:
    st.info("Няма открити стойностни прогнози за момента.")
    
