import streamlit as st
import requests

API_KEY = '2e086a4b6d758dec878ee7b5593405b1'
BASE_URL = 'https://api.the-odds-api.com/v4'

leagues = [
    'soccer_epl',
    'soccer_spain_la_liga',
    'soccer_germany_bundesliga',
    'soccer_italy_serie_a',
    'soccer_france_ligue_one',
    'soccer_netherlands_eredivisie',
    'soccer_portugal_liga'
]

st.title("Стойностни Залози - Автоматичен Анализ")
st.subheader("Цел: Да показва най-добрите залози от топ европейски лиги")
st.write("Зареждам мачове...")

def get_valid_markets(sport_key):
    try:
        url = f"{BASE_URL}/sports/{sport_key}/markets"
        params = {'apiKey': API_KEY}
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.warning(f"Проблем с пазарите за {sport_key} — {resp.status_code}")
            return []
    except Exception as e:
        st.error(f"Грешка при пазарите: {e}")
        return []

def get_odds(sport_key, markets):
    try:
        url = f"{BASE_URL}/sports/{sport_key}/odds"
        params = {
            'apiKey': API_KEY,
            'regions': 'eu',
            'markets': ','.join(markets),
            'oddsFormat': 'decimal',
            'dateFormat': 'iso'
        }
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.warning(f"Грешка за {sport_key}: {resp.status_code}")
            return []
    except Exception as e:
        st.error(f"Грешка при odds: {e}")
        return []

for league in leagues:
    with st.expander(f"Лига: {league}"):
        markets = get_valid_markets(league)
        if not markets:
            st.write("Няма налични пазари.")
            continue
        odds_data = get_odds(league, markets)
        if not odds_data:
            st.write("Няма мачове.")
            continue
        for match in odds_data:
            teams = match.get('teams', ['-', '-'])
            time = match.get('commence_time', 'N/A')
            st.markdown(f"### {teams[0]} vs {teams[1]}")
            st.caption(f"Начален час: {time}")
            for bookmaker in match.get('bookmakers', []):
                st.write(f"**{bookmaker.get('title', 'Unknown')}**")
                for market in bookmaker.get('markets', []):
                    st.write(f"Пазар: *{market.get('key')}*")
                    for outcome in market.get('outcomes', []):
                        name = outcome.get('name', 'N/A')
                        price = outcome.get('price', 'N/A')
                        st.write(f"- {name}: {price}")
