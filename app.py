import streamlit as st
import requests
from datetime import datetime
import pytz
import math

# === Настройки ===
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "uk,eu"
MARKETS = "h2h,totals,btts,spreads"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")
GOAL = 150  # Целева печалба в лева
DAYS = 5    # Срок в дни
bank = 500  # Начална банка

# === Streamlit UI ===
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# === Функция за изчисляване на залог ===
def calculate_bet_amount(bank, goal, days, odds):
    daily_goal = goal / days
    stake = daily_goal / (odds - 1)
    return round(stake / 10) * 10  # Закръглено на 10

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Реални мачове от Европа (днес)")
    st.caption("Данни от OddsAPI в реално време")

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.error(f"Грешка при зареждане на данни: {response.status_code} - {response.text}")
    else:
        data = response.json()
        value_bets = []

        for match in data:
            try:
                match_time = datetime.strptime(match['commence_time'], DATE_FORMAT)
                match_time_local = match_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
                if
