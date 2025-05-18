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

st.set_page_config(page_title="ТОП Стойностни Залози", layout="wide")
st.title("ТОП Стойностни Залози - Само Най-Добрите")
st.write("Показваме само мачовете с най-висока очаквана възвръщаемост (над 5%).")

value_bets = []

for league_key in EUROPE_LEAGUES:
    url = f"{BASE_URL}/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal&dateFormat=iso"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        if not matches:
            continue

        for match in matches:
            match_time = datetime.datetime.fromisoformat(match.get("commence_time", "").replace("Z", "+00:00"))
            if match_time <= datetime.datetime.utcnow():
                continue  # Прескачаме започналите мачове

            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_label = f"{home_team} vs {away_team}"

            all_odds = {}
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] not in ["h2h", "totals"]:
                        continue  # игнорираме други пазари, включително btts

                    for outcome in market.get("outcomes", []):
                        if market["key"] == "totals" and "point" in outcome:
                            selection_name = f"{outcome['name']} {outcome['point']}"
                        else:
                            selection_name = outcome["name"]

                        key = (market["key"], selection_name)
                        all_odds.setdefault(key, []).append(outcome["price"])

            for (market_key, name), prices in all_odds.items():
                if len(prices) < 2:
                    continue
                max_odd = max(prices)
                avg_odd = sum(prices) / len(prices)
                value_percent = calculate_value(max_odd, avg_odd)

                if value_percent >= 5:
                    value_bets.append({
                        "league": league_key.replace("soccer_", "").replace("_", " ").title(),
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
st.subheader("ТОП 10 Стойностни Залога за Деня")
if filtered_bets:
    for bet in filtered_bets[:10]:
        st.markdown(f"""
        <div style="border:1px solid #ddd; padding:10px; margin-bottom:10px; border-radius:10px; background-color:#f9f9f9;">
            <b>{bet['match']}</b> <span style="color:gray;">({bet['time']})</span><br>
            <i>Лига:</i> {bet['league']}<br>
            <i>Пазар:</i> {bet['market']}<br>
            <i>Залог:</i> <b>{bet['selection']}</b><br>
            <i>Коефициент:</i> <b>{bet['odd']:.2f}</b><br>
            <i>Стойност:</i> <b style="color:green;">+{bet['value']}%</b>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Няма стойностни залози с достатъчно висока стойност днес.")
