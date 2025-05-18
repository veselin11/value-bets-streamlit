import streamlit as st
import requests
import datetime
import pandas as pd

# Настройки
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

LEAGUE_NAMES = {
    "soccer_epl": "Англия - Висша лига",
    "soccer_spain_la_liga": "Испания - Ла Лига",
    "soccer_italy_serie_a": "Италия - Серия А",
    "soccer_germany_bundesliga": "Германия - Бундеслига",
    "soccer_france_ligue_one": "Франция - Лига 1",
    "soccer_netherlands_eredivisie": "Нидерландия - Ередивизи",
    "soccer_portugal_primeira_liga": "Португалия - Примейра Лига",
    "soccer_sweden_allsvenskan": "Швеция - Алсвенскан",
    "soccer_norway_eliteserien": "Норвегия - Елитсериен",
    "soccer_denmark_superliga": "Дания - Суперлига"
}

MARKET_NAMES = {
    "h2h": "Краен изход",
    "totals": "Над/Под голове"
}

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

# Заглавие и описание
st.title("ТОП Стойностни Залози")
st.caption("Фокус върху мачовете с най-висока очаквана възвръщаемост днес.")

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
            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_label = f"{home_team} vs {away_team}"

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

                if value_percent >= 5:
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

# Обработка
filtered_bets = remove_duplicates_by_match(value_bets)
filtered_bets.sort(key=lambda x: x["value"], reverse=True)

st.metric("Намерени стойностни залози", len(filtered_bets))

st.subheader("ТОП 10 Стойностни Залога за Деня")

if filtered_bets:
    for bet in filtered_bets[:10]:
        league_name = LEAGUE_NAMES.get(bet['league'], bet['league'])
        market_name = MARKET_NAMES.get(bet['market'], bet['market'])
        value_color = "green" if bet["value"] >= 10 else "orange"
        st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 10px; background-color: #f9f9f9; margin-bottom: 10px;">
                <h4 style="margin: 0;">{bet['match']} <span style="font-size: 14px;">({bet['time']})</span></h4>
                <p style="margin: 4px 0;">Лига: <strong>{league_name}</strong></p>
                <p style="margin: 4px 0;">Пазар: <strong>{market_name}</strong></p>
                <p style="margin: 4px 0;">Залог: <strong>{bet['selection']}</strong></p>
                <p style="margin: 4px 0;">Коефициент: <strong>{bet['odd']:.2f}</strong></p>
                <p style="margin: 4px 0;">Стойност: <strong style="color:{value_color};">+{bet['value']}%</strong></p>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("Няма стойностни залози с достатъчно висока стойност днес.")
