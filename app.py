import streamlit as st
import requests
from datetime import datetime

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

# За всяка лига задаваме валидни пазари, за да избегнем грешки 422
LEAGUE_MARKETS = {
    "soccer_epl": ["h2h"],  # само краен изход
    "soccer_spain_la_liga": ["h2h", "totals", "both_teams_to_score"],
    "soccer_germany_bundesliga": ["h2h", "totals"],
    "soccer_france_ligue_one": ["h2h", "both_teams_to_score"],
    "soccer_italy_serie_a": ["h2h", "totals", "both_teams_to_score"],
    "soccer_netherlands_eredivisie": ["h2h"],
    "soccer_portugal_primeira_liga": ["h2h", "totals"],
    # Можеш да добавиш още лиги и пазари
}

EUROPEAN_LEAGUES = list(LEAGUE_MARKETS.keys())

def fetch_odds(league):
    markets = LEAGUE_MARKETS.get(league, ["h2h"])  # По подразбиране само h2h
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": ",".join(markets),
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"Грешка при зареждане на {league}: {e}")
        return None

def calculate_value_bet(odds_list, true_prob=0.5):
    # Опитай се да изчислиш стойностния коефициент по прости правила:
    # Ако коефициентът е по-висок от 1/true_prob - стойностен залог
    # Тук true_prob може да се подобри с по-добър модел, сега е фиктивна стойност
    value_bets = []
    for bookmaker, odd in odds_list.items():
        try:
            odd_val = float(odd)
            implied_prob = 1 / odd_val
            if implied_prob < true_prob:  # Примерна стойностна логика
                value_bets.append((bookmaker, odd_val))
        except Exception:
            continue
    return value_bets

def analyze_and_display():
    st.title("Стойностни Залози - Автоматичен Анализ (ЕС)")
    st.write("Цел: Да показва само най-стойностните залози за деня - автоматично подбрани.\n")

    st.write("Зареждам мачове от основните европейски първенства...")

    total_value_bets = 0

    for league in EUROPEAN_LEAGUES:
        odds_data = fetch_odds(league)
        if odds_data is None:
            continue

        for match in odds_data:
            teams = match.get('teams', [])
            commence_time = match.get('commence_time', '')
            if not teams or not commence_time:
                continue
            # Форматиране на време
            try:
                dt_obj = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
                time_str = dt_obj.strftime("%Y-%m-%d %H:%M")
            except Exception:
                time_str = commence_time

            # Събиране на коефициенти за пазари
            for market in match.get('bookmakers', []):
                bookmaker_name = market.get('title', 'Unknown')
                for market_odds in market.get('markets', []):
                    # Анализирай само пазари, които сме задали за тази лига
                    if market_odds.get('key') not in LEAGUE_MARKETS[league]:
                        continue

                    outcomes = market_odds.get('outcomes', [])
                    # Изграждане речник букмейкър -> коефициент за всеки изход
                    odds_dict = {}
                    for outcome in outcomes:
                        odds_dict[outcome['name']] = outcome['price']

                    # Примерен анализ: стойностни залози за краен изход "Home", "Away", "Draw"
                    # Сложи тук твоята по-сложна логика за стойностни залози
                    value_bets = calculate_value_bet(odds_dict)
                    if value_bets:
                        total_value_bets += 1
                        st.write(f"**{teams[0]} vs {teams[1]}** ({time_str})")
                        st.write(f"Лига: {league}")
                        st.write(f"Пазар: {market_odds.get('key')}")
                        st.write(f"Букмейкър: {bookmaker_name}")
                        for bmk, odd_val in value_bets:
                            st.write(f"- Залог: {bmk}, Коефициент: {odd_val}")
                        st.write("---")

    if total_value_bets == 0:
        st.info("Няма открити стойностни залози за днес.")

if __name__ == "__main__":
    analyze_and_display()
