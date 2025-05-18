value_bets_app.py

import streamlit as st import requests import datetime import random

API ключ

API_KEY = "4474e2c1f44b1561daf6c481deb050cb" API_URL = "https://api.the-odds-api.com/v4/sports/soccer_european_major_leagues/odds/"

Инициализация на сесията

if "bankroll" not in st.session_state: st.session_state.bankroll = 500.0 if "bets_history" not in st.session_state: st.session_state.bets_history = [] if "todays_matches" not in st.session_state: st.session_state.todays_matches = []

st.set_page_config(page_title="Value Bets App", layout="centered")

st.title("Стойностни залози - Value Bets") st.markdown(f"Текуща банка: {st.session_state.bankroll:.2f} лв.")

Зареждане на реални мачове от API

@st.cache_data(show_spinner=True) def fetch_matches(): params = { "apiKey": API_KEY, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal", "dateFormat": "iso" } response = requests.get(API_URL, params=params) if response.status_code != 200: return [] data = response.json() matches = [] for item in data: commence = item.get("commence_time", "")[:16].replace("T", " ")

    
