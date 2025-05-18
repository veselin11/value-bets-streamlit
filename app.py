import streamlit as st
import requests
from datetime import datetime, timezone

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4"

# Пазари, които искаме да анализираме
DESIRED_MARKETS = ["h2h", "totals", "both_teams_to_score"]

st.title("Стойностни Залози - Автоматичен Анализ")

@st.cache_data(ttl=3600)
def get_sports():
    url = f"{BASE_URL}/sports"
    params = {"apiKey": API_KEY}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def get_valid_leagues():
    sports = get_sports()
    valid_leagues = []
    for sport in sports:
        if not sport.get("key", "").startswith("soccer_"):
            continue  # само футбол
        for league in sport.get("leagues", []):
            # Поне един от пазари да е наличен
            if any(m in DESIRED_MARKETS for m in league.get("markets", [])):
                valid_leagues.append(league["key"])
    return valid_leagues

def fetch_odds(league_key):
    url = f"{BASE_URL}/sports/{league_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": ",".join(DESIRED_MARKETS),
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 404:
        # Лигата не е намерена, игнорирай
        return []
    resp.raise_for_status()
    return resp.json()

def calculate_value(odds, probability_estimate=0.5):
    # Определяме стойност на залога: ако коефициент > 1 / вероятност => стойностен
    return odds > (1 / probability_estimate)

def analyze_value_bets(matches):
    value_bets = []
    for match in matches:
        try:
            teams = match["teams"]
            commence_time = match["commence_time"]
            game_time = datetime.fromisoformat(commence_time.replace("Z", "+00:00")).astimezone()
            bookmakers = match.get("bookmakers", [])

            for bookmaker in bookmakers:
                for market in bookmaker.get("markets", []):
                    market_key = market["key"]
                    for outcome in market.get("outcomes", []):
                        odds = outcome.get("price")
                        # Тук с примерно 0.5 вероятност за стойност, може да се подобри с по-сложен модел
                        if calculate_value(odds):
                            value_bets.append({
                                "teams": teams,
                                "time": game_time.strftime("%Y-%m-%d %H:%M"),
                                "league": match.get("sport_key"),
                                "bookmaker": bookmaker.get("title"),
                                "market": market_key,
                                "bet": outcome.get("name"),
                                "odds": odds
                            })
        except Exception as e:
            # Пропускаме грешки в конкретен мач
            continue
    return value_bets

def main():
    st.write("Зареждам мачове от основните европейски първенства...")
    valid_leagues = get_valid_leagues()

    all_value_bets = []

    for league in valid_leagues:
        try:
            matches = fetch_odds(league)
            if not matches:
                continue
            # Добавяме ключ за лигата към всеки мач
            for m in matches:
                m["sport_key"] = league
            bets = analyze_value_bets(matches)
            all_value_bets.extend(bets)
        except Exception as e:
            st.write(f"Грешка при зареждане на {league}: {str(e)}")

    if not all_value_bets:
        st.write("Няма открити стойностни залози за днес.")
        return

    st.write(f"Намерени {len(all_value_bets)} стойностни залози:")
    for bet in all_value_bets:
        st.markdown(f"**{bet['teams'][0]} vs {bet['teams'][1]}** ({bet['time']})")
        st.markdown(f"- Лига: {bet['league']}")
        st.markdown(f"- Букмейкър: {bet['bookmaker']}")
        st.markdown(f"- Пазар: {bet['market']}")
        st.markdown(f"- Залог: {bet['bet']}")
        st.markdown(f"- Коефициент: {bet['odds']}")
        st.markdown("---")

if __name__ == "__main__":
    main()
