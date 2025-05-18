import streamlit as st
import requests
import datetime
from collections import defaultdict

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

EUROPE_LEAGUES = [
    "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga",
    "soccer_france_ligue_one", "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga",
    "soccer_russia_premier_league", "soccer_austria_bundesliga", "soccer_sweden_allsvenskan",
    "soccer_norway_eliteserien", "soccer_denmark_superliga", "soccer_league_of_ireland"
]

st.title("Стойностни Залози - Автоматичен Анализ (ЕС)")
st.write("Зареждам стойностни залози от основните европейски първенства...")

# Чекбокс за показване на всички
show_all = st.checkbox("Показвай всички стойностни залози", value=False)

value_bets = []
grouped_bets = defaultdict(list)

def is_value_bet(odd, prob_threshold=0.6):
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
            match_label = f"{home_team} vs {away_team} ({match_time.strftime('%Y-%m-%d %H:%M')})"

            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market.get("outcomes", []):
                            odd = outcome.get("price")
                            name = outcome.get("name")
                            if odd and odd > 1.5 and is_value_bet(odd):
                                bet = {
                                    "league": league_key,
                                    "match": match_label,
                                    "bookmaker": bookmaker.get("title"),
                                    "selection": name,
                                    "odd": odd
                                }
                                value_bets.append(bet)
                                key = (match_label, name)
                                grouped_bets[key].append(odd)
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            st.warning(f"Лига '{league_key}' не е намерена (404), пропускам...")
        else:
            st.error(f"Грешка при зареждане на {league_key}: {http_err}")
    except Exception as e:
        st.error(f"Грешка при зареждане на {league_key}: {e}")

# Покажи всички залози (ако е маркирано)
if show_all and value_bets:
    st.subheader("Всички открити стойностни залози:")
    for bet in value_bets:
        st.markdown(
            f"**{bet['match']}**  \n"
            f"Букмейкър: {bet['bookmaker']}  \n"
            f"Залог: {bet['selection']}  \n"
            f"Коефициент: {bet['odd']:.2f}"
        )

# Покажи ТОП 5 стойностни залога
ranked_bets = []
for (match, selection), odds in grouped_bets.items():
    avg_odd = sum(odds) / len(odds)
    max_odd = max(odds)
    diff = (max_odd - avg_odd) / avg_odd
    if diff >= 0.05:  # минимум 5% стойност
        ranked_bets.append({
            "match": match,
            "selection": selection,
            "avg_odd": avg_odd,
            "max_odd": max_odd,
            "value_diff": diff
        })

top_bets = sorted(ranked_bets, key=lambda x: x["value_diff"], reverse=True)[:5]

if top_bets:
    st.markdown("---")
    st.subheader("ТОП 5 стойностни залога:")
    for bet in top_bets:
        st.markdown(
            f"**{bet['match']}**  \n"
            f"Залог: {bet['selection']}  \n"
            f"Среден коефициент: {bet['avg_odd']:.2f}  \n"
            f"Най-добър коефициент: {bet['max_odd']:.2f}  \n"
            f"Стойност: {bet['value_diff']*100:.1f}%"
        )
else:
    st.info("Няма ТОП стойностни залози за показване в момента.")

# --- Статистика ---
st.markdown("---")
st.subheader("Статистика")
st.write("Проследяване на печалби, ROI и успеваемост ще бъде добавено при свързване с база данни или автоматично от заложна платформа.")
