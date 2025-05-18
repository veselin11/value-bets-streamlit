import streamlit as st
import requests
import datetime
from typing import List, Dict

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
REGIONS = "eu"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"

# Основни европейски лиги (валидирани)
LEAGUES = [
    "soccer_epl",  # England Premier League
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_greece_super_league",
    "soccer_switzerland_superleague",
    "soccer_denmark_superliga",
    "soccer_austria_bundesliga",
    "soccer_czech_republic_first_league",
    "soccer_croatia_1_hnl",
    "soccer_sweden_allsvenskan",
    "soccer_norway_eliteserien",
    "soccer_finland_veikkausliiga",
    "soccer_poland_ekstraklasa",
    "soccer_serbia_super_liga",
    "soccer_romania_liga_1",
    "soccer_russia_premier_league",
    "soccer_turkey_superlig",
    "soccer_belgium_jupiler_league",
    "soccer_scotland_premiership"
]

st.title("Стойностни Залози - Автоматичен Анализ (ЕС)")
st.write("Цел: Показване само на най-стойностните залози за деня")

value_bets = []
all_checked = 0

for league in LEAGUES:
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={MARKETS}&oddsFormat={ODDS_FORMAT}&dateFormat={DATE_FORMAT}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        for match in data:
            all_checked += 1
            home_team = match.get("home_team")
            away_team = match.get("away_team")
            commence_time = match.get("commence_time")
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "h2h":
                        outcomes = market.get("outcomes", [])
                        max_odd = max([o['price'] for o in outcomes])
                        avg_odd = sum([o['price'] for o in outcomes]) / len(outcomes)
                        for outcome in outcomes:
                            value = (outcome['price'] - avg_odd) / avg_odd
                            if value > 0.10:  # само стойностни залози >10%
                                value_bets.append({
                                    "teams": f"{home_team} vs {away_team}",
                                    "time": commence_time,
                                    "bookmaker": bookmaker['title'],
                                    "bet_on": outcome['name'],
                                    "odd": outcome['price'],
                                    "value": round(value * 100, 2),
                                    "league": league
                                })
    except requests.exceptions.RequestException as e:
        st.warning(f"Грешка при зареждане на {league}: {e}")

if value_bets:
    st.subheader("Намерени стойностни залози:")
    for bet in value_bets:
        st.markdown(f"**{bet['teams']}** ({bet['time']})")
        st.markdown(f"Лига: `{bet['league']}`")
        st.markdown(f"Букмейкър: {bet['bookmaker']}")
        st.markdown(f"Залог: **{bet['bet_on']}** при коефициент **{bet['odd']}**")
        st.markdown(f"**Стойност на залога: +{bet['value']}%**")
        st.markdown("---")
else:
    st.info("Няма открити стойностни залози за днес.")

# Статистика
st.subheader("Статистика")
st.markdown(f"Общо проверени мачове: **{all_checked}**")
st.markdown(f"Намерени стойностни залози: **{len(value_bets)}**")
if all_checked > 0:
    st.markdown(f"Процент стойностни залози: **{round(len(value_bets) / all_checked * 100, 2)}%**")
    
