import streamlit as st
import requests
import datetime

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

# Валидни лиги към момента (без тези, които дават 404)
EUROPE_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_russia_premier_league",
    "soccer_austria_bundesliga",
    "soccer_sweden_allsvenskan",
    "soccer_norway_eliteserien",
    "soccer_denmark_superliga",
    "soccer_league_of_ireland"
]

st.title("Стойностни Залози - Автоматичен Анализ (ЕС)")

st.write("Зареждам мачове от всички основни европейски първенства...")

value_bets = []

def is_value_bet(odd, prob_threshold=0.5):
    """Оценка дали коефициентът е стойностен спрямо вероятност."""
    implied_prob = 1 / odd
    return implied_prob < prob_threshold

for league_key in EUROPE_LEAGUES:
    url = f"{BASE_URL}/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        if not matches:
            continue

        for match in matches:
            commence_time = match.get("commence_time", "")
            match_time = datetime.datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")

            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market.get("outcomes", []):
                            odd = outcome.get("price")
                            name = outcome.get("name")
                            if odd and odd > 1.5 and is_value_bet(odd, prob_threshold=0.6):
                                value_bets.append({
                                    "league": league_key,
                                    "match": f"{home_team} vs {away_team}",
                                    "time": match_time.strftime("%Y-%m-%d %H:%M"),
                                    "bookmaker": bookmaker.get("title"),
                                    "selection": name,
                                    "odd": odd
                                })
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            st.warning(f"Лига '{league_key}' не е намерена (404), пропускам...")
        else:
            st.error(f"Грешка при зареждане на {league_key}: {http_err}")
    except Exception as e:
        st.error(f"Грешка при зареждане на {league_key}: {e}")

if value_bets:
    st.subheader("Намерени стойностни залози:")
    for bet in value_bets:
        st.markdown(
            f"**{bet['match']}** ({bet['time']})  \n"
            f"Лига: {bet['league']}  \n"
            f"Букмейкър: {bet['bookmaker']}  \n"
            f"Залог: {bet['selection']}  \n"
            f"Коефициент: {bet['odd']:.2f}"
        )
else:
    st.info("Няма открити стойностни залози за днес.")

# --- Статистика ---
st.markdown("---")
st.subheader("Статистика")
st.write("Печалби, загуби и общо залози (трябва да се въвеждат ръчно или автоматично при интеграция с реална база).")
st.write("Понастоящем няма реализирани залози.")
