import streamlit as st
import requests
import datetime
import pandas as pd

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
    "soccer_sweden_allsvenskan",
    "soccer_norway_eliteserien",
    "soccer_denmark_superliga"
]

def calculate_value(odd, avg_odd):
    if not avg_odd or avg_odd == 0:
        return 0
    return round((odd - avg_odd) / avg_odd * 100, 2)

def remove_duplicates_by_match(bets):
    unique = {}
    for bet in bets:
        key = (bet['match'], bet['selection'])
        if key not in unique or unique[key]['value'] < bet['value']:
            unique[key] = bet
    return list(unique.values())

st.title("ТОП Стойностни Залози - Само Най-Добрите")
st.write("Показваме само мачовете с най-висока очаквана възвръщаемост.")

value_bets = []

for league_key in EUROPE_LEAGUES:
    url = f"{BASE_URL}/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal&dateFormat=iso"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        if not matches:
            continue

        for match in matches:
            match_time = datetime.datetime.fromisoformat(match.get("commence_time", "").replace("Z", "+00:00"))
            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_label = f"{home_team} vs {away_team}"

            # Събиране на всички коефициенти за всяка селекция
            all_odds = {}
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        key = (market["key"], outcome["name"])
                        all_odds.setdefault(key, []).append(outcome["price"])

            for (market_key, name), prices in all_odds.items():
                if len(prices) < 2:
                    continue
                max_odd = max(prices)
                avg_odd = sum(prices) / len(prices)
                value_percent = calculate_value(max_odd, avg_odd)

                if value_percent >= 5:  # праг на стойностен залог
                    value_bets.append({
                        "league": league_key,
                        "match": match_label,
                        "time": match_time.strftime("%Y-%m-%d %H:%M"),
                        "selection": name,
                        "market": market_key,
                        "odd": max_odd,
                        "value": value_percent
                    })
    except Exception as e:
        st.error(f"Грешка при зареждане на {league_key}: {e}")

# Премахване на дубли и сортиране по стойност
filtered_bets = remove_duplicates_by_match(value_bets)
filtered_bets.sort(key=lambda x: x["value"], reverse=True)

# Показваме само топ 10
st.subheader("ТОП 10 Стойностни Залога")
if filtered_bets:
    for bet in filtered_bets[:10]:
        st.markdown(
            f"**{bet['match']}** ({bet['time']})  \
            Лига: `{bet['league']}`  \
            Пазар: `{bet['market']}`  \
            Залог: **{bet['selection']}**  \
            Коефициент: **{bet['odd']:.2f}**  \
            Стойност: **+{bet['value']}%**"
        )
else:
    st.info("Няма стойностни залози с достатъчно висока стойност днес.")
    
