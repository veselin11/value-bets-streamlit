import streamlit as st
import requests
import datetime
import random

# API ключ и URL
API_KEY = "4474e2c1f44b1561daf6c481deb050cb"
API_URL = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso"

# Начална сесия
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500.0
if "bets_history" not in st.session_state:
    st.session_state.bets_history = []

# Заглавие
st.set_page_config(page_title="Value Bets App", layout="centered")
st.title("Стойностни залози - Value Bets")

# Зареждане на мачове
matches = []
try:
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        for match in data:
            teams = match.get("teams", [])
            if len(teams) == 2:
                odds_data = match.get("bookmakers", [])[0]["markets"][0]["outcomes"]
                for outcome in odds_data:
                    if outcome["name"] == teams[0]:  # Залагаме на домакина
                        odds = outcome["price"]
                        if odds >= 1.5 and odds <= 2.5:
                            matches.append({
                                "match": f"{teams[0]} vs {teams[1]}",
                                "prediction": "1",
                                "odds": odds
                            })
    else:
        st.error(f"Грешка при зареждане на мачове: {response.status_code}")
except Exception as e:
    st.error(f"Възникна грешка: {e}")

# Ако няма мачове – примерни
if not matches:
    st.warning("Няма реални мачове или стойностни залози – използваме примерни.")
    matches = [
        {"match": "Барселона vs Хетафе", "prediction": "1", "odds": 1.55},
        {"match": "Верона vs Болоня", "prediction": "2", "odds": 2.10},
        {"match": "Брюж vs Андерлехт", "prediction": "X", "odds": 3.20},
    ]

# Показване на банка
st.markdown(f"**Текуща банка:** {st.session_state.bankroll:.2f} лв.")

# Въвеждане на залог
bet_amount = st.number_input("Сума за залог (лв.):", min_value=1, max_value=int(st.session_state.bankroll), value=50, step=1)
selected = st.radio("Избери мач:", [f"{m['match']} | {m['prediction']} | {m['odds']}" for m in matches])

# Натискане на бутон
if st.button("Заложи"):
    match = next((m for m in matches if f"{m['match']} | {m['prediction']} | {m['odds']}" == selected), None)
    if match:
        win = random.random() < 1 / match["odds"]
        result = "Печалба" if win else "Загуба"
        if win:
            profit = bet_amount * (match["odds"] - 1)
            st.session_state.bankroll += profit
        else:
            st.session_state.bankroll -= bet_amount
        st.session_state.bets_history.append({
            "match": match["match"],
            "prediction": match["prediction"],
            "odds": match["odds"],
            "amount": bet_amount,
            "result": result,
            "date": str(datetime.date.today())
        })
        st.success(f"{match['match']} | {result} | Банка: {st.session_state.bankroll:.2f} лв.")

# История
st.subheader("История на залозите")
if st.session_state.bets_history:
    for bet in st.session_state.bets_history[::-1]:
        st.write(f"{bet['date']} | {bet['match']} | Прогноза: {bet['prediction']} | Коеф: {bet['odds']} | {bet['result']} | Залог: {bet['amount']} лв.")
else:
    st.info("Все още няма направени залози.")
