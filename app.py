import streamlit as st
import requests
from datetime import datetime
import pytz

# Настройки
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
REGION = "eu"  # Европа
MARKET = "h2h"  # 1X2 (победа/равен/загуба)
DATE_FORMAT = "%Y-%m-%d"

st.set_page_config(page_title="Стойностни залози", layout="wide")
st.title("Стойностни залози – Реални мачове от Европа (днес)")

# Дата днес във формат ISO
today = datetime.now(pytz.timezone("Europe/Sofia")).strftime(DATE_FORMAT)

# Извличане на коефициенти от API
@st.cache_data(ttl=600)
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "markets": MARKET,
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error("Грешка при зареждане на данни от OddsAPI.")
        st.stop()
    return response.json()

# Показване на резултатите
data = get_odds()

if not data:
    st.warning("Няма налични мачове за днес.")
else:
    for match in data:
        commence_time = match["commence_time"]
        match_date = commence_time[:10]

        if match_date != today:
            continue

        teams = match["home_team"] + " vs " + match["away_team"]
        st.subheader(teams)
        st.text(f"Час: {commence_time[11:16]}")

        for bookmaker in match.get("bookmakers", []):
            st.markdown(f"**{bookmaker['title']}**")
            cols = st.columns(len(bookmaker["markets"][0]["outcomes"]))
            for i, outcome in enumerate(bookmaker["markets"][0]["outcomes"]):
                with cols[i]:
                    st.metric(outcome["name"], f"{outcome['price']}")

        st.markdown("---")
