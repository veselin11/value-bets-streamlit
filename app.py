import streamlit as st
import random
import datetime

# Начална настройка на сесията
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500.0
if "bets_history" not in st.session_state:
    st.session_state.bets_history = []
if "todays_matches" not in st.session_state:
    st.session_state.todays_matches = [
        {"match": "Барселона vs Хетафе", "odds": 1.55, "prediction": "1", "selected": False},
        {"match": "Верона vs Болоня", "odds": 2.10, "prediction": "2", "selected": False},
        {"match": "Брюж vs Андерлехт", "odds": 2.45, "prediction": "X", "selected": False}
    ]

st.set_page_config(page_title="Value Bets App", layout="centered")

# CSS за по-добър дизайн и мобилна съвместимост
st.markdown("""
<style>
    .main {
        max-width: 600px;
        margin: auto;
        padding: 10px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .match-box {
        background-color: #f0f2f6;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 8px;
    }
    button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 15px;
        border-radius: 5px;
        cursor: pointer;
    }
    button:disabled {
        background-color: #a5a5a5;
        cursor: not-allowed;
    }
    h2 {
        color: #333333;
    }
    .bankroll {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main">', unsafe_allow_html=True)

st.title("Стойностни залози - Value Bets App")

st.markdown(f'<div class="bankroll">Текуща банка: {st.session_state.bankroll:.2f} лв.</div>', unsafe_allow_html=True)

st.header("Днешни мачове за залагане")

bet_amount = st.number_input("Въведи сума за залог (лв.):", min_value=1, max_value=int(st.session_state.bankroll), value=50, step=1)

matches_display = [
    f"{m['match']} | Прогноза: {m['prediction']} | Коефициент: {m['odds']}"
    for m in st.session_state.todays_matches
]

selected_match_index = st.radio(
    "Избери мач за залог:",
    options=matches_display,
    index=0
)

def place_bet():
    idx = matches_display.index(selected_match_index)
    match = st.session_state.todays_matches[idx]
    if match["selected"]:
        st.warning(f"Вече си заложил на мача: {match['match']}")
        return
    if bet_amount > st.session_state.bankroll:
        st.error("Нямаш достатъчно пари в банката за този залог.")
        return
    # Изчисляване на резултат
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
    st.success(f"{match['match']} | Прогноза: {match['prediction']} | Коефициент: {match['odds']} | {result} | Банка: {st.session_state.bankroll:.2f} лв.")

if st.button("Заложи"):
    place_bet()

st.header("История на залозите")
if st.session_state.bets_history:
    for bet in st.session_state.bets_history:
        st.write(f"{bet['date']} | {bet['match']} | Прогноза: {bet['prediction']} | Коефициент: {bet['odds']} | {bet['result']} | Заложено: {bet['amount']} лв.")
else:
    st.write("Все още няма направени залози.")

st.markdown('</div>', unsafe_allow_html=True)
