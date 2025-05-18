import streamlit as st
import requests
import datetime
from collections import defaultdict

# Конфигурация
API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

EUROPE_LEAGUES = [
    "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a",
    "soccer_germany_bundesliga", "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga",
    "soccer_russia_premier_league", "soccer_austria_bundesliga",
    "soccer_sweden_allsvenskan", "soccer_norway_eliteserien",
    "soccer_denmark_superliga", "soccer_league_of_ireland"
]

# Заглавие
st.title("Стойностни Залози - Европейски Мачове")
st.write("Автоматичен анализ на стойностни коефициенти от надеждни лиги.")

value_bets = []

# --- Извличане на данни ---
for league_key in EUROPE_LEAGUES:
    url = f"{BASE_URL}/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        if not matches:
            continue

        for match in matches:
            match_time = datetime.datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00"))
            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_name = f"{home_team} vs {away_team}"

            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market.get("outcomes", []):
                            odd = outcome.get("price")
                            name = outcome.get("name")
                            if odd and odd > 1.5:
                                value_bets.append({
                                    "league": league_key,
                                    "match": match_name,
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

# --- Групиране и филтриране за ТОП 5 залога ---
grouped_bets = defaultdict(list)
for bet in value_bets:
    key = (bet['match'], bet['selection'])
    grouped_bets[key].append(bet['odd'])

top_bets = []
for (match, selection), odds in grouped_bets.items():
    avg_odd = sum(odds) / len(odds)
    max_odd = max(odds)
    value_diff = (max_odd - avg_odd) / avg_odd
    if value_diff >= 0.05:  # Стойностен праг 5%
        top_bets.append({
            "match": match,
            "selection": selection,
            "avg_odd": avg_odd,
            "max_odd": max_odd,
            "value_diff": value_diff
        })

top_bets_sorted = sorted(top_bets, key=lambda x: x["value_diff"], reverse=True)[:5]

# --- Визуализация ---
if value_bets:
    st.subheader("Всички открити стойностни залози:")
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

# --- ТОП 5 най-стойностни залога ---
st.markdown("---")
st.subheader("ТОП 5 стойностни залога (по разлика между среден и максимален коефициент):")

if top_bets_sorted:
    for bet in top_bets_sorted:
        st.markdown(
            f"**{bet['match']}**  \n"
            f"Залог: `{bet['selection']}`  \n"
            f"Среден коефициент: {bet['avg_odd']:.2f} | Максимален коефициент: {bet['max_odd']:.2f}  \n"
            f"Стойностна разлика: **{bet['value_diff'] * 100:.2f}%**"
        )
else:
    st.info("Няма достатъчно стойностни разлики за топ залози.")

# --- Статистика (бъдещо надграждане) ---
st.markdown("---")
st.subheader("Статистика (демо)")
st.write("В бъдеще ще добавим проследяване на ROI, успехи и загуби по тип залог и лига.")
