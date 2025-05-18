# Автоматичен анализатор на стойностни залози – Поддържани пазари: 1X2, Над/Под 2.5, Гол/Гол

import streamlit as st
import requests
from datetime import datetime

# Настройки
API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
REGIONS = "eu"
MARKETS = ["h2h", "over_under", "btts"]  # 1X2, над/под, гол/гол
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"
VALUE_THRESHOLD = 1.05  # Минимална стойност за стойностен залог

# Основни лиги от Европа
LEAGUES = [
    "soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga",
    "soccer_italy_serie_a", "soccer_france_ligue_one", "soccer_netherlands_eredivisie",
    "soccer_greece_super_league", "soccer_portugal_primeira_liga", "soccer_denmark_superliga",
    "soccer_norway_eliteserien", "soccer_sweden_allsvenskan", "soccer_switzerland_superleague",
    "soccer_austria_bundesliga", "soccer_bulgaria_first_professional", "soccer_czech_republic_first_league"
]

# Показване на заглавие
st.title("Стойностни Залози – Автоматичен Анализ")
st.markdown("**Цел:** Да показва само най-стойностните залози за деня – автоматично подбрани.")

# Функция за изчисляване на стойност
def calculate_value(odd, implied_prob):
    if implied_prob == 0:
        return 0
    return odd * (1 - implied_prob)

# Заявка към API
def fetch_odds(league, market):
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": market,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": DATE_FORMAT
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.warning(f"Грешка при зареждане на {league}: {response.status_code}")
        return []
    return response.json()

# Обработка и показване на стойностни залози
def analyze_and_display():
    found_value_bets = False
    for league in LEAGUES:
        for market in MARKETS:
            data = fetch_odds(league, market)
            for match in data:
                teams = match['teams']
                commence = match['commence_time'][:16].replace("T", " ")
                for bookmaker in match.get('bookmakers', []):
                    for outcome in bookmaker.get('markets', []):
                        if market not in outcome['key']:
                            continue
                        for selection in outcome.get('outcomes', []):
                            odd = selection.get('price')
                            implied_prob = 1 / odd if odd else 0
                            value = calculate_value(odd, implied_prob)
                            if value >= VALUE_THRESHOLD:
                                found_value_bets = True
                                st.markdown(f"**{teams[0]} vs {teams[1]}**  \n"
                                            f"Лига: `{league}`  \n"
                                            f"Пазар: `{market}`  \n"
                                            f"Избор: `{selection['name']}`  \n"
                                            f"Коефициент: `{odd}`  \n"
                                            f"Букмейкър: `{bookmaker['title']}`  \n"
                                            f"Стойност: `{round(value, 2)}`  \n"
                                            f"Час: `{commence}`  \n---")
    if not found_value_bets:
        st.info("Няма открити стойностни залози за днес.")

# Изпълнение
analyze_and_display()
