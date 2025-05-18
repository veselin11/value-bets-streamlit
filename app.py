import streamlit as st
import requests
import datetime
import random

API_KEY = "4474e2c1f44b1561daf6c481deb050cb"

st.set_page_config(page_title="Value Bets App", layout="centered")

if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500.0
if "bets_history" not in st.session_state:
    st.session_state.bets_history = []
if "sports" not in st.session_state:
    st.session_state.sports = []

# Функция за зареждане на спортове
def load_sports():
    url = "https://api.the-odds-api.com/v4/sports/"
    params = {"apiKey": API_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"Грешка при зареждане на спортове: {resp.status_code}")
        return []

if not st.session_state.sports:
    st.session_state.sports = load_sports()

sport_options = {sport["title"]: sport["key"] for sport in st.session_state.sports}
selected_sport_title = st.selectbox("Избери спорт", list(sport_options.keys()))

selected_sport_key = sport_options[selected_sport_title]

st.write(f"Избран спорт: **{selected_sport_title}**")

# Зареждане на мачове с коефициенти
def load_matches(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h,totals",
        "oddsFormat": "decimal"
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json()
    else:
        st.error(f"Грешка при зареждане на мачове: {resp.status_code}")
        return []

matches = load_matches(selected_sport_key)

def is_value_bet(odd, threshold=2.0):
    # Примерна дефиниция: коефициент > 2.0 е стойностен
    return odd > threshold

st.header("Стойностни залози за днес")

value_bets = []

for match in matches:
    # Примерен анализ: взимаме първия букмейкър и първия пазар
    if "bookmakers" not in match or not match["bookmakers"]:
        continue
    bookmaker = match["bookmakers"][0]
    markets = bookmaker.get("markets", [])
    for market in markets:
        if market["key"] == "h2h":
            for i, outcome in enumerate(market["outcomes"]):
                odd = outcome["price"]
                if is_value_bet(odd):
                    value_bets.append({
                        "match": match["home_team"] + " vs " + match["away_team"],
                        "start_time": match["commence_time"],
                        "bookmaker": bookmaker["title"],
                        "outcome": outcome["name"],
                        "odd": odd
                    })

if not value_bets:
    st.write("Няма ясни стойностни залози за днес.")
else:
    for idx, bet in enumerate(value_bets):
        st.write(f"{idx + 1}. {bet['match']} | Изход: {bet['outcome']} | Коефициент: {bet['odd']:.2f} | Букмейкър: {bet['bookmaker']}")

# Залог
bet_idx = st.number_input("Избери номер на мач за залог:", min_value=1, max_value=len(value_bets), step=1)
bet_amount = st.number_input("Въведи сума за залог (лв.):", min_value=1, max_value=int(st.session_state.bankroll), value=50, step=1)

def place_bet():
    bet = value_bets[bet_idx - 1]
    odd = bet["odd"]
    win = random.random() < 1 / odd
    result = "Печалба" if win else "Загуба"
    if win:
        profit = bet_amount * (odd - 1)
        st.session_state.bankroll += profit
    else:
        st.session_state.bankroll -= bet_amount

    st.session_state.bets_history.append({
        "match": bet["match"],
        "outcome": bet["outcome"],
        "odd": odd,
        "amount": bet_amount,
        "result": result,
        "date": str(datetime.date.today())
    })

    st.success(f"Резултат: {result} | Текуща банка: {st.session_state.bankroll:.2f} лв.")

if st.button("Заложи"):
    if len(value_bets) > 0:
        place_bet()
    else:
        st.warning("Няма стойностни залози за залагане.")

# История на залозите
st.header("История на залозите")
if st.session_state.bets_history:
    for bet in st.session_state.bets_history:
        st.write(f"{bet['date']} | {bet['match']} | Изход: {bet['outcome']} | Коефициент: {bet['odd']:.2f} | {bet['result']} | Заложено: {bet['amount']} лв.")
else:
    st.write("Все още няма направени залози.")
