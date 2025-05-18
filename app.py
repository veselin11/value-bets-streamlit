import streamlit as st
import requests
import datetime
import random

# Конфигурация
API_KEY = "4474e2c1f44b1561daf6c481deb050cb"
BOOKMAKER = "pinnacle"  # Може да промениш по избор
REGION = "eu"  # Европа
MARKETS = ["h2h", "totals"]  # 1X2 и Над/Под

# Сесия
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500.0
if "bets_history" not in st.session_state:
    st.session_state.bets_history = []

# Layout
st.set_page_config(page_title="Value Bets", layout="centered")
st.title("Стойностни залози за днес")

# Функция за зареждане на мачове
def fetch_matches():
    url = f"https://api.the-odds-api.com/v4/sports/soccer_european_championship/odds/?regions={REGION}&markets={','.join(MARKETS)}&oddsFormat=decimal&apiKey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as e:
        st.error("Проблем с API връзката.")
        return []

# Оценка на стойностен залог
def calculate_value(odds, implied_prob):
    return round(odds * implied_prob - 1, 2)

# Залози
def place_bet(match_info, amount):
    win = random.random() < 1 / match_info["odds"]
    result = "Печалба" if win else "Загуба"
    if win:
        profit = amount * (match_info["odds"] - 1)
        st.session_state.bankroll += profit
    else:
        st.session_state.bankroll -= amount

    st.session_state.bets_history.append({
        "match": match_info["name"],
        "market": match_info["market"],
        "odds": match_info["odds"],
        "amount": amount,
        "result": result,
        "date": str(datetime.date.today())
    })
    st.success(f"{match_info['name']} | {match_info['market']} | Коефициент: {match_info['odds']} | {result} | Наличност: {st.session_state.bankroll:.2f} лв.")

# Зареждане и филтриране
matches = fetch_matches()
value_bets = []

for match in matches:
    for bookmaker in match.get("bookmakers", []):
        if bookmaker["key"] != BOOKMAKER:
            continue
        for market in bookmaker["markets"]:
            if market["key"] == "h2h":
                outcomes = market["outcomes"]
                for outcome in outcomes:
                    implied_prob = 0.33  # фиксирано за тест, може да се замени с модел
                    value = calculate_value(outcome["price"], implied_prob)
                    if value > 0.15:
                        value_bets.append({
                            "name": f"{match['home_team']} vs {match['away_team']}",
                            "market": outcome["name"],
                            "odds": outcome["price"],
                            "value": value
                        })

# Показване на стойностни мачове
if value_bets:
    st.markdown(f"### Най-добрите стойностни залози за днес ({len(value_bets)})")
    for i, match in enumerate(value_bets):
        with st.container():
            st.markdown(f"**{match['name']}**")
            st.markdown(f"Прогноза: {match['market']}, Коефициент: {match['odds']}, Стойност: {match['value']}")
            amount = st.number_input(f"Сума за залог на {match['name']}", min_value=1, max_value=int(st.session_state.bankroll), value=10, key=f"amt_{i}")
            if st.button(f"Заложи на {match['name']}", key=f"bet_{i}"):
                place_bet(match, amount)
else:
    st.info("Няма стойностни мачове за днес или проблем с API.")

# История
st.header("История на залозите")
if st.session_state.bets_history:
    for bet in st.session_state.bets_history:
        st.write(f"{bet['date']} | {bet['match']} | {bet['market']} | Коефициент: {bet['odds']} | {bet['result']} | {bet['amount']} лв.")
else:
    st.write("Все още няма залози.")

st.markdown(f"### Банка: {st.session_state.bankroll:.2f} лв.")
