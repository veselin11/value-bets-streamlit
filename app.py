import streamlit as st
import requests

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

# Списък с основни европейски първенства (валидни за The Odds API)
LEAGUES = [
    "soccer_epl",
    "soccer_la_liga",
    "soccer_serie_a",
    "soccer_bundesliga",
    "soccer_ligue_one",
    "soccer_uefa_champions_league",
    "soccer_eredivisie",
    "soccer_russian_premier_league",
    "soccer_scottish_premiership"
]

MARKETS = ["h2h", "totals", "both_teams_to_score"]

def fetch_odds(league):
    url = f"{BASE_URL}/{league}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": ",".join(MARKETS),
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        st.error(f"Грешка при зареждане на {league}: {e}")
        return []

def calculate_value(odds, probability_estimate=0.7):
    # Ако коефициентът е по-голям от 1/probability_estimate => стойностен залог
    return odds > (1 / probability_estimate)

def analyze_value_bets(matches):
    value_bets = []

    for match in matches:
        teams = match.get("teams", ["N/A", "N/A"])
        commence_time = match.get("commence_time", "")
        bookmakers = match.get("bookmakers", [])

        for bookmaker in bookmakers:
            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")
                for outcome in market.get("outcomes", []):
                    odds = outcome.get("price")
                    if odds is None:
                        continue
                    # Debug печат на коефициентите
                    st.write(f"DEBUG: {teams} | {market_key} | {outcome.get('name')} = {odds}")
                    if calculate_value(odds):
                        value_bets.append({
                            "teams": teams,
                            "time": commence_time,
                            "league": match.get("sport_key", "unknown"),
                            "bookmaker": bookmaker.get("title", "unknown"),
                            "market": market_key,
                            "bet": outcome.get("name"),
                            "odds": odds
                        })
    return value_bets

def main():
    st.title("Стойностни Залози - Автоматичен Анализ")
    st.write("Цел: Да показва само най-стойностните залози за деня - автоматично подбрани.\n")
    st.write("Зареждам мачове от основните европейски първенства...\n")

    all_matches = []
    for league in LEAGUES:
        matches = fetch_odds(league)
        st.write(f"Намерени {len(matches)} мача в {league}")
        all_matches.extend(matches)

    value_bets = analyze_value_bets(all_matches)

    if not value_bets:
        st.info("Няма открити стойностни залози за днес.")
    else:
        st.success(f"Намерени {len(value_bets)} стойностни залози:")
        for bet in value_bets:
            st.write(f"**{bet['teams'][0]} vs {bet['teams'][1]}** ({bet['time']})")
            st.write(f"Лига: {bet['league']}")
            st.write(f"Букмейкър: {bet['bookmaker']}")
            st.write(f"Пазар: {bet['market']}")
            st.write(f"Залог: {bet['bet']}")
            st.write(f"Коефициент: {bet['odds']}")
            st.write("---")

if __name__ == "__main__":
    main()
