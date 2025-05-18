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
        padding: 20px 10px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .match-box {
        background-color: #f0f2f6;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 8px;
        border: 1px solid #ccc;
        transition: border-color 0.3s ease;
    }
    .match-box.selected {
        border: 2px solid #4CAF50 !important;
    }
    button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 1rem;
        transition: background-color 0.3s ease;
        width: 100%;
        margin-top: 10px;
    }
    button:hover:not(:disabled) {
        background-color: #45a049;
    }
    button:disabled {
        background-color: #a5a5a5;
        cursor: not-allowed;
    }
    h2, h1 {
        color: #333333;
        text-align: center;
    }
    .bankroll {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 20px;
        text-align: center;
    }
    .stRadio > label {
        font-weight: 600;
        font-size: 1rem;
    }
    @media (max-width: 480px) {
        .main {
            padding: 15px 5px;
        }
        button {
            font-size: 1.1rem;
            padding: 12px 0;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main">', unsafe_allow_html=True)

st.title("Стойностни залози - Value Bets App")

st.markdown(f'<div class="bankroll">Текуща банка: {st.session_state.bankroll:.2f} лв.</div>', unsafe_allow_html=True)

bet_amount = st.number_input(
    "Въведи сума за залог (лв.):",
    min_value=1,
    max_value=int(st.session_state.bankroll),
    value=50,
    step=1
)

# Избор на мач
matches_display = [
    f"{m['match']} | Прогноза: {m['prediction']} | Коефициент: {m['odds']}"
    for m in st.session_state.todays_matches
]
selected_match_index = st.radio("Избери мач за залог
