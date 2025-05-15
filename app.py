import streamlit as st
import requests
from datetime import datetime
import pytz
import math

# === Конфигурация ===
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "eu,uk"
MARKETS = "h2h,totals,btts,spreads"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

# === Настройки на целта ===
GOAL = 150  # Целева печалба
DAYS = 5    # Срок в дни
bank = 500  # Начална банка

# === Функция за изчисление на залога ===
def calculate_bet_amount(bank, goal, days, odds):
    daily_goal = goal / days
    stake = daily_goal / (odds - 1)
    return round(stake / 10) * 10  # Кръгла стойност

# === Streamlit UI ===
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# === Таб 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Прогнози за днес")
    st.caption("Източник: OddsAPI")

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.error(f"Грешка при зареждане на данни: {response.status_code}")
    else:
        data = response.json()
        value_bets = []

        for match in data:
            # Прескачане на мачове без време
            try:
                match_time = datetime.strptime(match['commence_time'], DATE_FORMAT)
                match_time_local = match_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
                if match_time_local.date() != datetime.now(local_tz).date():
                    continue
            except:
                continue

            if 'bookmakers' not in match or not match['bookmakers']:
                continue

            best_odds = {}

            for bookmaker in match['bookmakers']:
                for market in bookmaker['markets']:
                    market_type = market['key']
                    if market_type in ['h2h', 'totals', 'btts', 'spreads']:
                        for outcome in market['outcomes']:
                            outcome_name = outcome['name']
                            label = f"{market_type.upper()}: {outcome_name}"
                            price = outcome['price']
                            if label not in best_odds or price > best_odds[label]['price']:
                                best_odds[label] = {
                                    'price': price,
                                    'bookmaker': bookmaker['title']
                                }

            if len(best_odds) < 2:
                continue

            inv_probs = [1 / info['price'] for info in best_odds.values()]
            fair_prob_sum = sum(inv_probs)

            for label, info in best_odds.items():
                fair_prob = (1 / info['price']) / fair_prob_sum
                value = info['price'] * fair_prob
                if value > 1.05:
                    stake = calculate_bet_amount(bank, GOAL, DAYS, info['price'])
                    value_bets.append({
                        "Мач": f"{match['home_team']} vs {match['away_team']}",
                        "Пазар": label,
                        "Коефициент": info['price'],
                        "Букмейкър": info['bookmaker'],
                        "Value %": round((value - 1) * 100, 2),
                        "Залог (лв)": stake,
                        "Час": match_time_local.strftime("%H:%M")
                    })

        if value_bets:
            sorted_bets = sorted(value_bets, key=lambda x: -x["Value %"])
            st.dataframe(sorted_bets, use_container_width=True)
        else:
            st.info("Няма стойностни залози за днес.")

# === Таб 2: История ===
with tabs[1]:
    st.header("История на залозите")
    st.write("Тук ще се виждат направените залози. (В процес на разработка)")

# === Таб 3: Настройки ===
with tabs[2]:
    st.header("Настройки")
    st.write("В бъдеще тук ще могат да се избират лиги, маркети, банка и цел.")
