import streamlit as st
import requests
import random
from datetime import date

API_KEY = "cb4a5917231d8b20dd6b85ae9d025e6e"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# Зареждане на мачове от API за днес
def fetch_todays_matches():
    today_str = date.today().isoformat()
    url = f"{BASE_URL}/fixtures"
    params = {"date": today_str}
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    matches = []
    if data["results"] == 0:
        return matches
    for item in data["response"]:
        home = item["teams"]["home"]["name"]
        away = item["teams"]["away"]["name"]
        fixture_id = item["fixture"]["id"]
        # Опитваме да вземем коефициенти от първия букмейкър, ако има
        odds = {"1": None, "X": None, "2": None}
        bookmakers = item.get("bookmakers", [])
        if bookmakers:
            bets = bookmakers[0].get("bets", [])
            for bet in bets:
                if bet["name"] == "Match Winner":
                    for val in bet["values"]:
                        odds[val["name"]] = float(val["odd"])
                    break
        matches.append({
            "match": f"{home} vs {away}",
            "odds": odds,
            "selected": False
        })
    return matches

# Инициализация Streamlit сесия
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500
if "bets_history" not in st.session_state:
    st.session_state.bets_history = []
if "todays_matches" not in st.session_state:
    st.session_state.todays_matches = fetch_todays_matches()

st.title("Value Bets App - Стойностни залози")

if not st.session_state.todays_matches:
    st.write("Няма налични мачове за днес или проблем с API.")
else:
    st.write("Днешни мачове с реални коефициенти:")

    for i, match in enumerate(st.session_state.todays_matches):
        odds = match["odds"]
        st.write(f"{i+1}. {match['match']} | 1: {odds['1']} | X: {odds['X']} | 2: {odds['2']}")

    match_index = st.number_input("Избери номер на мач за залагане:", min_value=1, max_value=len(st.session_state.todays_matches), value=1) - 1

    bet_option = st.selectbox("Избери прогноза:", options=["1", "X", "2"])
    max_bet = st.session_state.bankroll
    bet_amount = st.number_input(f"Въведи сума за залог (до {max_bet:.2f} лв.):", min_value=1.0, max_value=max_bet, value=10.0)

    if st.button("Заложи"):
        match = st.session_state.todays_matches[match_index]
        if match["selected"]:
            st.warning("Вече си заложил на този мач.")
        else:
            odd_value = match["odds"].get(bet_option)
            if odd_value is None:
                st.error("Няма наличен коефициент за тази прогноза.")
            else:
                win = random.random() < 1 / odd_value
                result = "Печалба" if win else "Загуба"
                if win:
                    profit = bet_amount * (odd_value - 1)
                    st.session_state.bankroll += profit
                else:
                    st.session_state.bankroll -= bet_amount
                match["selected"] = True
                st.session_state.bets_history.append({
                    "match": match["match"],
                    "prediction": bet_option,
                    "odds": odd_value,
                    "amount": bet_amount,
                    "result": result
                })
                st.success(f"{result}! Текуща банка: {st.session_state.bankroll:.2f} лв.")

    if st.session_state.bets_history:
        st.header("История на залозите")
        for bet in st.session_state.bets_history:
            st.write(f"{bet['match']} | Прогноза: {bet['prediction']} | Коефициент: {bet['odds']} | Сума: {bet['amount']} | Резултат: {bet['result']}")

    st.markdown(f"### Текуща банка: {st.session_state.bankroll:.2f} лв.")
