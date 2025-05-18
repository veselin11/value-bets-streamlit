value_bets_app.py

import streamlit as st import requests import datetime import random

API ключ

API_KEY = "4474e2c1f44b1561daf6c481deb050cb" API_URL = "https://api.the-odds-api.com/v4/sports/soccer_european_major_leagues/odds/"

Инициализация на сесията

if "bankroll" not in st.session_state: st.session_state.bankroll = 500.0 if "bets_history" not in st.session_state: st.session_state.bets_history = [] if "todays_matches" not in st.session_state: st.session_state.todays_matches = []

st.set_page_config(page_title="Value Bets App", layout="centered")

st.title("Стойностни залози - Value Bets") st.markdown(f"Текуща банка: {st.session_state.bankroll:.2f} лв.")

Зареждане на реални мачове от API

@st.cache_data(show_spinner=True) def fetch_matches(): params = { "apiKey": API_KEY, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal", "dateFormat": "iso" } response = requests.get(API_URL, params=params) if response.status_code != 200: return [] data = response.json() matches = [] for item in data: commence = item.get("commence_time", "")[:16].replace("T", " ") teams = item.get("home_team", "") + " vs " + item.get("away_team", "") for bookmaker in item.get("bookmakers", []): for market in bookmaker.get("markets", []): if market["key"] == "h2h": outcomes = market.get("outcomes", []) if len(outcomes) == 3: odds = max(outcomes, key=lambda x: x["price"]) value = 1 / odds["price"] < 0.35  # критерий за стойностен залог if value: matches.append({ "match": teams, "start": commence, "prediction": odds["name"], "odds": odds["price"], "selected": False }) return matches

if not st.session_state.todays_matches: st.session_state.todays_matches = fetch_matches()

if not st.session_state.todays_matches: st.warning("Няма стойностни залози за днес или има проблем с API-то.") else: st.header("Избери залог") bet_amount = st.number_input("Сума за залог (лв.):", min_value=1, max_value=int(st.session_state.bankroll), value=50)

selected_match = st.radio("Мачове:", [
    f"{m['start']} | {m['match']} | Прогноза: {m['prediction']} | Коефициент: {m['odds']}" for m in st.session_state.todays_matches
])

def place_bet():
    idx = [
        f"{m['start']} | {m['match']} | Прогноза: {m['prediction']} | Коефициент: {m['odds']}" for m in st.session_state.todays_matches
    ].index(selected_match)
    match = st.session_state.todays_matches[idx]

    if match["selected"]:
        st.warning("Вече си заложил на този мач.")
        return

    win = random.random() < 1 / match["odds"]
    result = "Печалба" if win else "Загуба"

    if win:
        profit = bet_amount * (match["odds"] - 1)
        st.session_state.bankroll += profit
    else:
        st.session_state.bankroll -= bet_amount

    match["selected"] = True
    st.session_state.bets_history.append({
        "match": match["match"],
        "prediction": match["prediction"],
        "odds": match["odds"],
        "amount": bet_amount,
        "result": result,
        "date": str(datetime.date.today())
    })
    st.success(f"{match['match']} | {result} | Текуща банка: {st.session_state.bankroll:.2f} лв.")

if st.button("Заложи на избрания мач"):
    place_bet()

st.header("История на залозите") if st.session_state.bets_history: for bet in st.session_state.bets_history: st.write(f"{bet['date']} | {bet['match']} | {bet['prediction']} | {bet['odds']} | {bet['result']} | {bet['amount']} лв.") else: st.info("Все още няма направени залози.")

