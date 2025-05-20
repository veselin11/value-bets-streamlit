import streamlit as st
import requests
import datetime
import pandas as pd

# API ключ
ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

st.set_page_config(layout="wide")
st.title("Стойностни футболни залози – Value Bets")

@st.cache_data(ttl=600)
def load_all_matches_from_the_odds_api():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {
        "regions": "eu",
        "markets": "h2h,totals,btts",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "apiKey": ODDS_API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error(f"Грешка при зареждане на мачове: {response.status_code} – {response.text}")
        return []

    return response.json()

def display_matches(matches):
    if not matches:
        st.warning("Няма налични мачове в момента.")
        return

    for match in matches:
        home = match.get('home_team', 'Неизвестен')
        away = match.get('away_team', 'Неизвестен')
        commence = match.get('commence_time', 'Неизвестно време')
        bookmakers = match.get('bookmakers', [])

        with st.expander(f"{home} vs {away} – {commence}"):
            for bookie in bookmakers:
                st.markdown(f"### {bookie['title']}")
                for market in bookie.get('markets', []):
                    st.write(f"**Пазар: {market['key']}**")
                    for outcome in market.get('outcomes', []):
                        st.write(f"{outcome['name']}: {outcome['price']}")

def main():
    st.info("Зареждане на реални мачове и коефициенти от всички налични лиги...")
    matches = load_all_matches_from_the_odds_api()
    display_matches(matches)

if __name__ == "__main__":
    main()
    
