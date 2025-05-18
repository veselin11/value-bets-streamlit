import streamlit as st
import requests
from datetime import datetime

API_KEY = "4474e2c1f44b1561daf6c481deb050cb"
API_URL = "https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
SPORTS = [
    "soccer_brazil_campeonato",
    "soccer_denmark_superliga",
    "soccer_finland_veikkausliiga",
    "soccer_japan_j_league",
    "soccer_league_of_ireland",
    "soccer_norway_eliteserien",
    "soccer_spain_segunda_division",
    "soccer_sweden_allsvenskan",
    "soccer_sweden_superettan",
    "soccer_usa_mls"
]

st.title("Стойностни Залози - Автоматичен Анализ")
st.markdown("**Цел:** Да показва само най-стойностните залози за деня - автоматично подбрани.")

profit = st.session_state.get("profit", 0.0)
initial_bankroll = st.session_state.get("initial_bankroll", 500.0)

found_bets = []

for sport_key in SPORTS:
    try:
        url = API_URL.format(sport_key=sport_key)
        response = requests.get(url, params={
            "apiKey": API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        })

        response.raise_for_status()
        data = response.json()

        for match in data:
            home = match["home_team"]
            away = match["away_team"]
            commence_time = datetime.fromisoformat(match["commence_time"]).strftime("%d-%m %H:%M")

            for bookmaker in match.get("bookmakers", []):
                outcomes = bookmaker.get("markets", [])[0].get("outcomes", [])
                if len(outcomes) < 2:
                    continue

                odds = {o["name"]: o["price"] for o in outcomes}
                max_odds = max(odds.values())
                implied_prob = 1 / max_odds
                fair_odds = 1 / implied_prob

                if max_odds > fair_odds * 1.05:  # >=5% стойностен залог
                    bet = {
                        "Мач": f"{home} vs {away}",
                        "Час": commence_time,
                        "Пазар": max(odds, key=odds.get),
                        "Коефициент": max_odds,
                        "Стойност": round((max_odds * implied_prob - 1) * 100, 2)
                    }
                    found_bets.append(bet)
    except Exception as e:
        continue

if found_bets:
    st.success("Открити стойностни залози за днес:")
    for bet in found_bets:
        st.write(f"**{bet['Мач']}** - {bet['Час']} | Пазар: {bet['Пазар']} | Коеф: {bet['Коефициент']} | Стойност: {bet['Стойност']}%")

        if st.button(f"Заложи на {bet['Мач']} - {bet['Пазар']}", key=bet['Мач']+bet['Пазар']):
            profit += (bet['Коефициент'] - 1) * 50  # Печалба при успех
            st.session_state["profit"] = profit
            st.success(f"Добавен залог. Потенциална печалба: {round((bet['Коефициент'] - 1) * 50, 2)} лв.")
else:
    st.warning("Няма открити стойностни залози за днес.")

st.markdown("---")
st.subheader("Статистика")
st.write(f"Начален капитал: {initial_bankroll:.2f} лв.")
st.write(f"Текуща печалба/загуба: {profit:.2f} лв.")
st.write(f"Текущ баланс: {initial_bankroll + profit:.2f} лв.")
