import streamlit as st
import requests
import datetime

API_KEY = "4474e2c1f44b1561daf6c481deb050cb"
REGION = "eu"
MARKET = "h2h"
BOOKMAKER = "pinnacle"

st.set_page_config(page_title="Стойностни залози", layout="centered")

st.title("Стойностни залози (Value Bets App)")
st.write("Основна цел: показване на реални мачове с **висока стойност** според коефициентите и изчислена вероятност.")

def calculate_value(odds, implied_prob):
    if odds <= 1:
        return 0
    return round((odds * implied_prob - 1), 2)

@st.cache_data(ttl=1800)
def fetch_matches():
    url = "https://api.the-odds-api.com/v4/sports/soccer_europe/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "markets": MARKET,
        "oddsFormat": "decimal"
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error(f"Грешка при зареждане на мачове: {response.status_code}")
        return []
    return response.json()

matches = fetch_matches()
value_bets = []

for match in matches:
    if not isinstance(match, dict) or "bookmakers" not in match:
        continue
    for bookmaker in match["bookmakers"]:
        if bookmaker["key"] != BOOKMAKER:
            continue
        for market in bookmaker.get("markets", []):
            if market["key"] != MARKET:
                continue
            for outcome in market.get("outcomes", []):
                implied_prob = 0.33  # фиксирано за демонстрация
                value = calculate_value(outcome["price"], implied_prob)
                if value > 0.15:
                    value_bets.append({
                        "match": f"{match.get('home_team')} vs {match.get('away_team')}",
                        "time": match.get("commence_time", "")[:16].replace("T", " "),
                        "selection": outcome["name"],
                        "odds": outcome["price"],
                        "value": value
                    })

if value_bets:
    st.subheader("Най-стойностни залози за днес:")
    for bet in value_bets:
        st.markdown(f"""
        **Мач:** {bet['match']}  
        **Час:** {bet['time']}  
        **Залог:** {bet['selection']}  
        **Коефициент:** {bet['odds']}  
        **Стойност:** {bet['value']:.2f}  
        ---
        """)
else:
    st.warning("Няма открити стойностни залози за днес или проблем с API.")
