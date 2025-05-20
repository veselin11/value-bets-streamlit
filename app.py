# app.py

import streamlit as st
import requests
from datetime import datetime
import pytz

from utils.odds import fetch_value_bets
from utils.stats import fetch_team_stats, TEAM_ID_MAPPING

st.set_page_config(page_title="Стойностни футболни залози", layout="wide")
st.title("Най-стойностни футболни залози днес")

value_bets = fetch_value_bets()

if not value_bets:
    st.warning("Няма стойностни залози в момента.")
else:
    for bet in value_bets:
        match = bet["match"]
        market = bet["market"]
        outcome = bet["outcome"]
        bookmaker = bet["bookmaker"]
        odds = bet["odds"]
        value = bet["value"]
        commence_time = datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00"))
        commence_time = commence_time.astimezone(pytz.timezone("Europe/Sofia"))

        with st.expander(f'{match["home_team"]} vs {match["away_team"]} — {market.upper()} — {outcome} @ {odds} ({value*100:.1f}% стойност)'):
            st.markdown(f"**Час:** {commence_time.strftime('%d.%m.%Y %H:%M')}")
            st.markdown(f"**Букмейкър:** {bookmaker}")
            st.markdown(f"**Пазар:** {market}")
            st.markdown(f"**Изход:** {outcome}")
            st.markdown(f"**Коефициент:** {odds}")
            st.markdown(f"**Стойност:** {value:.2f}")

            # Статистика – само ако и двата отбора са в TEAM_ID_MAPPING
            home_team = match["home_team"]
            away_team = match["away_team"]

            show_stats = home_team in TEAM_ID_MAPPING or away_team in TEAM_ID_MAPPING

            if show_stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**{home_team} – последни мачове:**")
                    stats = fetch_team_stats(home_team)
                    if stats:
                        st.write(stats)
                    else:
                        st.write("Няма налична статистика.")
                with col2:
                    st.markdown(f"**{away_team} – последни мачове:**")
                    stats = fetch_team_stats(away_team)
                    if stats:
                        st.write(stats)
                    else:
                        st.write("Няма налична статистика.")
