import streamlit as st
import requests
import datetime
import random

API_KEY = "cb4a5917231d8b20dd6b85ae9d025e6e"
API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"

# Инициализация на сесията
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500.0
if "bets_history" not in st.session_state:
    st.session_state.bets_history = []
if "matches" not in st.session_state:
    st.session_state.matches = []

st.set_page_config(page_title="Value Bets App", layout="centered")

st.title("Стойностни залози - Value Bets App")

def fetch_matches():
    try:
        params = {
            "apiKey": API_KEY,
            "regions": "eu",  # Европа
            "markets": "h2h",  # Краен изход
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Филтриране за стойностни залози (value > 0.1)
        matches = []
        for match in data:
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") == "h2h":
                        for outcome in market.get("outcomes", []):
                            # Изчисляване на value: (нашата прогноза тук да е най-висок коефициент)
                            value = outcome["price"] - 1 / (1 / outcome["price"])
                            # (Тук за пример ползваме коефициент > 1.8 за стойностна залога)
                            if outcome["price"] >= 1.8:
                                matches.append({
                                    "match": f"{match['home_team']} vs {match['away_team']}",
                                    "start_time": match["commence_time"][:16].replace("T", " "),
                                    "bookmaker": bookmaker["title"],
                                    "odds": outcome["price"],
                                    "prediction": outcome["name"],
                                })
        return matches
    except Exception as e:
        st.error(f"Грешка при зареждане на мачове: {e}")
        return []

if st.button("Обнови мачове за днес"):
    st.session_state.matches = fetch_matches()

if not st.session_state.matches:
    st.info("Натиснете бутона 'Обнови мачове за днес' за да заредите стойностни залози.")
else:
    st.subheader("Стойностни залози за днес")
    for i, match in enumerate(st.session_state.matches):
        st.markdown(f"**{match['start_time']}** — {match['match']}\n\nПрогноза: {match['prediction']} | Коефициент: {match['odds']} | Букмейкър: {match['bookmaker']}")
        bet_amount = st.number_input(f"Сума за залог (лв.) на мач {i+1}", min_value=1, max_value=int(st.session_state.bankroll), value=10, key=f"bet_amount_{i}")
        if st.button(f"Заложи на мач {i+1}", key=f"bet_btn_{i}"):
            if bet_amount > st.session_state.bankroll:
                st.error("Нямаш достатъчно пари в банката за този залог.")
            else:
                win = random.random() < 1 / match["odds"]  # Симулиране на резултат
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
                st.success(f"{match['match']} | {result} | Текуща банка: {st.session_state.bankroll:.2f} лв.")

    # Статистика
    total_bets = len(st.session_state.bets_history)
    wins = sum(1 for bet in st.session_state.bets_history if bet["result"] == "Печалба")
    losses = total_bets - wins
    st.subheader("Статистика")
    st.write(f"Общо залози: {total_bets}")
    st.write(f"Печалби: {wins}")
    st.write(f"Загуби: {losses}")
    st.write(f"Текуща банка: {st.session_state.bankroll:.2f} лв.")

    # История на залозите
    st.subheader("История на залозите")
    for bet in st.session_state.bets_history:
        st.write(f"{bet['date']} | {bet['match']} | Прогноза: {bet['prediction']} | Коефициент: {bet['odds']} | {bet['result']} | Заложено: {bet['amount']} лв.")
