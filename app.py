import streamlit as st
import requests

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

# Списък с основни футболни лиги, които знаем, че са валидни
LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_belgium_first_div",
    "soccer_russia_premier_league",
    "soccer_usa_mls",
]

def fetch_odds(league_key):
    url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h,totals,both_teams_to_score",
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        st.warning(f"Грешка при зареждане на {league_key}: {e}")
        return []

def calculate_value(odds, true_prob):
    return (odds * true_prob) - 1

def analyze_matches():
    value_bets = []

    for league in LEAGUES:
        matches = fetch_odds(league)
        if not matches:
            continue

        for match in matches:
            teams = match.get("teams", ["Unknown", "Unknown"])
            commence_time = match.get("commence_time", "Unknown time")

            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        # Примерно изчисляване на вероятности от коефициенти за 3 изхода
                        for outcome in market["outcomes"]:
                            odds = outcome["price"]
                            # Тук трябва да се сметне true probability по сложна формула или използвай по-опростена
                            # За пример ще приемем, че true_prob е обратната стойност на средния коефициент
                            true_prob = 1 / odds
                            value = calculate_value(odds, true_prob)
                            if value > 0.05:  # Праг за стойностен залог
                                value_bets.append({
                                    "teams": teams,
                                    "time": commence_time,
                                    "market": "h2h",
                                    "outcome": outcome["name"],
                                    "odds": odds,
                                    "value": round(value, 3),
                                    "league": league,
                                })
                    # Можеш да добавиш анализ и за други пазари тук

    return value_bets

def main():
    st.title("Стойностни Залози - Автоматичен Анализ")
    st.write("Цел: Да показва само най-стойностните залози за деня - автоматично подбрани.")
    st.write("Зареждам мачове от основните европейски първенства...")

    value_bets = analyze_matches()

    if value_bets:
        st.write(f"Намерени {len(value_bets)} стойностни залози:")
        for bet in value_bets:
            st.write(f"**{bet['teams'][0]} vs {bet['teams'][1]}** ({bet['time']}) - {bet['market']} - {bet['outcome']} @ {bet['odds']} (Value: {bet['value']}) [{bet['league']}]")
    else:
        st.write("Няма открити стойностни залози за днес.")

if __name__ == "__main__":
    main()
