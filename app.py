import streamlit as st
import requests
from datetime import datetime
import pytz

# Настройки и API ключове
THE_ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
FOOTBALL_DATA_API_KEY = "81e6d3a2f88f4d0d8a6b45f4c8d21568"
SPORT = "soccer"
REGIONS = "eu"
MARKETS = "h2h,totals,btts"
BOOKMAKERS = "pinnacle,bet365,unibet,bwin"

TEAM_ID_MAPPING = {
    "Manchester City": 65,
    "Arsenal": 57,
    "Liverpool": 64,
    "Chelsea": 61,
    "Tottenham": 73,
    "Manchester United": 66,
    "Aston Villa": 58,
    "Brighton": 397,
    "West Ham": 563,
    "Newcastle": 67,
    "Everton": 62,
    "Fulham": 63,
    "Wolves": 76,
    "Crystal Palace": 354,
    "Bournemouth": 1044,
    "Brentford": 402,
    "Nottingham Forest": 351,
    "Burnley": 328,
    "Sheffield United": 356,
    "Luton": 389
}

@st.cache_data
def get_live_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": THE_ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "decimal",
        "bookmakers": BOOKMAKERS
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Грешка при зареждане на коефициенти.")
        return []

@st.cache_data
def get_team_stats(team_name):
    if team_name not in TEAM_ID_MAPPING:
        return None
    team_id = TEAM_ID_MAPPING[team_name]
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json().get("matches", [])
        wins = sum(1 for m in matches if m["score"]["winner"] == "HOME_TEAM" and m["homeTeam"]["id"] == team_id or
                                     m["score"]["winner"] == "AWAY_TEAM" and m["awayTeam"]["id"] == team_id)
        goals_for = sum(m["score"]["fullTime"]["home"] if m["homeTeam"]["id"] == team_id else m["score"]["fullTime"]["away"] for m in matches)
        goals_against = sum(m["score"]["fullTime"]["away"] if m["homeTeam"]["id"] == team_id else m["score"]["fullTime"]["home"] for m in matches)
        return {"wins": wins, "goals_for": goals_for, "goals_against": goals_against}
    return None

def calculate_value(odds, est_prob):
    if odds == 0:
        return 0
    implied_prob = 1 / odds
    value = est_prob - implied_prob
    return round(value, 3)

st.title("Стойностни залози – Всички лиги")
matches = get_live_odds()

if not matches:
    st.warning("Няма налични мачове в момента.")
else:
    match_names = [f'{m["home_team"]} vs {m["away_team"]} - {m.get("sport_title", "")}' for m in matches]
    selection = st.selectbox("Избери мач", match_names)
    match = matches[match_names.index(selection)]

    st.subheader(f'{match["home_team"]} vs {match["away_team"]}')
    start_time = datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00")).astimezone(pytz.timezone("Europe/Sofia"))
    st.caption(f"Начален час: {start_time.strftime('%d.%m.%Y %H:%M')} ч.")
    st.caption(f"Лига: {match.get('sport_title', 'Unknown')}")

    st.markdown("### Статистики (ако са налични):")
    col1, col2 = st.columns(2)
    with col1:
        stats_home = get_team_stats(match["home_team"])
        if stats_home:
            st.metric("Победи", stats_home["wins"])
            st.metric("Голове за", stats_home["goals_for"])
            st.metric("Голове против", stats_home["goals_against"])
        else:
            st.write("Няма статистика за домакините.")
    with col2:
        stats_away = get_team_stats(match["away_team"])
        if stats_away:
            st.metric("Победи", stats_away["wins"])
            st.metric("Голове за", stats_away["goals_for"])
            st.metric("Голове против", stats_away["goals_against"])
        else:
            st.write("Няма статистика за гостите.")

    st.markdown("### Коефициенти и стойност:")
    for bookmaker in match["bookmakers"]:
        name = bookmaker["title"]
        for market in bookmaker["markets"]:
            st.markdown(f"**{name} - {market['key']}**")
            for outcome in market["outcomes"]:
                label = outcome["name"]
                odds = outcome["price"]
                est_prob = 0.35  # Тук може да добавим ML/статистика по-късно
                value = calculate_value(odds, est_prob)
                st.write(f"{label}: {odds} | Стойност: {value}")
