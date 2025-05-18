import streamlit as st
import requests
import datetime
from statistics import mean

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

# Лиги, които ще проверяваме (топ 5 + други надеждни)
EUROPE_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_austria_bundesliga"
]

st.title("Стойностни Залози - Автоматичен Анализ (ЕС)")

st.write("Зареждам мачове от всички основни европейски първенства...")

value_bets = []

def implied_probability(odd):
    return 1 / odd if odd > 0 else 0

def is_value_bet(odd, avg_odd, threshold_pct=0.07):
    """Определя дали коефициентът е с поне threshold_pct по-висок от средния (value bet)"""
    if avg_odd == 0:
        return False
    diff = odd - avg_odd
    return diff / avg_odd >= threshold_pct

def filter_active_leagues(leagues, min_matches=2):
    """Филтрира лиги с минимум активни мачове."""
    active = []
    for league in leagues:
        url = f"{BASE_URL}/{league}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso"
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            if len(data) >= min_matches:
                active.append(league)
        except:
            pass
    return active

# Филтрираме само активните лиги с достатъчно мачове
active_leagues = filter_active_leagues(EUROPE_LEAGUES)

if not active_leagues:
    st.warning("Няма активни лиги с достатъчно мачове днес.")
else:
    for league_key in active_leagues:
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

                # Събираме всички коефициенти за пазар h2h от всички букмейкъри
                all_h2h_odds = []
                for bookmaker in match.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "h2h":
                            for outcome in market.get("outcomes", []):
                                odd = outcome.get("price")
                                if odd:
                                    all_h2h_odds.append(odd)

                if not all_h2h_odds:
                    continue

                avg_odd = mean(all_h2h_odds)

                # Проверяваме за value bets при всеки букмейкър и пазар
                for bookmaker in match.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "h2h":
                            for outcome in market.get("outcomes", []):
                                odd = outcome.get("price")
                                name = outcome.get("name")
                                if odd and odd > 1.3 and is_value_bet(odd, avg_odd, threshold_pct=0.07):
                                    value_bets.append({
                                        "league": league_key,
                                        "match": f"{home_team} vs {away_team}",
                                        "time": match_time.strftime("%Y-%m-%d %H:%M"),
                                        "bookmaker": bookmaker.get("title"),
                                        "selection": name,
                                        "odd": odd,
                                        "avg_odd": avg_odd,
                                        "value_pct": (odd - avg_odd) / avg_odd * 100
                                    })

        except Exception as e:
            st.error(f"Грешка при зареждане на {league_key}: {e}")

if value_bets:
    # Сортираме по най-висока стойностна разлика
    value_bets = sorted(value_bets, key=lambda x: x["value_pct"], reverse=True)

    st.subheader("Намерени стойностни залози:")
    for bet in value_bets:
        st.markdown(
            f"**{bet['match']}** ({bet['time']})  \n"
            f"Лига: {bet['league']}  \n"
            f"Букмейкър: {bet['bookmaker']}  \n"
            f"Залог: {bet['selection']}  \n"
            f"Коефициент: {bet['odd']:.2f}  \n"
            f"Среден коефициент на пазара: {bet['avg_odd']:.2f}  \n"
            f"Стойност на залога: {bet['value_pct']:.1f}%"
        )
else:
    st.info("Няма открити стойностни залози за днес.")

# --- Базова статистика ---
st.markdown("---")
st.subheader("Статистика")

if 'stats' not in st.session_state:
    st.session_state.stats = {"bets": 0, "wins": 0, "losses": 0}

st.write(f"Общо залози: {st.session_state.stats['bets']}")
st.write(f"Печалби: {st.session_state.stats['wins']}")
st.write(f"Загуби: {st.session_state.stats['losses']}")
st.write("ROI: N/A (трябва да се добавят реални данни за резултатите)")
