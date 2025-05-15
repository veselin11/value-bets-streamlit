import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="Стойностни залози", layout="wide")
st.title("Стойностни залози – Реални мачове от Европа (днес)")

API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
REGIONS = "eu"  # Европа
MARKETS = "h2h"  # Краен резултат
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

params = {
    "apiKey": API_KEY,
    "regions": REGIONS,
    "markets": MARKETS,
    "oddsFormat": "decimal"
}

# Вземи днешна дата (в UTC)
today = datetime.utcnow().date()

try:
    response = requests.get(ODDS_API_URL, params=params)
    data = response.json()

    shown = 0
    for match in data:
        match_time_utc = datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00"))
        match_date = match_time_utc.date()

        if match_date == today:
            home = match["home_team"]
            away = match["away_team"]
            bookmakers = match.get("bookmakers", [])

            st.subheader(f"{home} vs {away}")
            st.write(f"Час: {match_time_utc.strftime('%H:%M')} UTC")

            if bookmakers:
                for bm in bookmakers[:1]:  # Показваме само първия букмейкър
                    st.markdown(f"**Букмейкър:** {bm['title']}")
                    for outcome in bm["markets"][0]["outcomes"]:
                        st.write(f"{outcome['name']}: коефициент {outcome['price']}")
            st.markdown("---")
            shown += 1

    if shown == 0:
        st.warning("Няма мачове за днес от избрания регион.")
except Exception as e:
    st.error(f"Грешка при зареждане на данни: {e}")
