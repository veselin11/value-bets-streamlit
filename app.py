import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import time

API_KEY = st.secrets["ODDS_API_KEY"]

LEAGUES = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
    "Serie A": "soccer_italy_serie_a",
    "Ligue 1": "soccer_france_ligue_one",
    "Champions League": "soccer_uefa_champs_league"
}

@st.cache_data(ttl=300)
def fetch_odds(league_code):
    url = f"https://api.the-odds-api.com/v4/sports/{league_code}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    else:
        st.error(f"Грешка при зареждане на коефициенти за {league_code}")
        return []

def filter_favorites_today(games, threshold=1.5):
    filtered = []
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    for game in games:
        try:
            commence = datetime.fromisoformat(game["commence_time"].replace("Z", "+00:00"))
            if not (start_of_day <= commence <= end_of_day):
                continue
            bookmakers = game.get("bookmakers", [])
            if not bookmakers:
                continue
            markets = bookmakers[0].get("markets", [])
            h2h = next((m for m in markets if m["key"] == "h2h"), None)
            if not h2h:
                continue
            outcomes = h2h["outcomes"]
            min_odd = min(o["price"] for o in outcomes)
            if min_odd <= threshold:
                favorite = min(outcomes, key=lambda x: x["price"])
                filtered.append({
                    "league": game["sport_title"],
                    "match": f"{game['home_team']} vs {game['away_team']}",
                    "commence_time": commence,
                    "favorite_team": favorite["name"],
                    "initial_odd": favorite["price"],
                    "game_id": game["id"]
                })
        except Exception:
            continue

    filtered.sort(key=lambda x: x["commence_time"])
    return filtered

st.title("Live Фаворити за Днес ⚽")

# Sidebar настройки
st.sidebar.header("Настройки на сигнала")
odd_increase_threshold = st.sidebar.slider("Минимално покачване за сигнал", 0.05, 1.0, 0.2, 0.05)
refresh_interval = st.sidebar.slider("Интервал за обновяване (сек.)", 30, 600, 300, 30)
enable_sound = st.sidebar.checkbox("Включи звуков сигнал при промяна", value=False)

selected_league_name = st.sidebar.selectbox("Избери лига", list(LEAGUES.keys()))
selected_league_code = LEAGUES[selected_league_name]

all_games = fetch_odds(selected_league_code)
favorites = filter_favorites_today(all_games, threshold=1.5)

if "prev_odds" not in st.session_state:
    st.session_state.prev_odds = {}

table_data = []
alerts = []

for fav in favorites:
    current_game = next((g for g in all_games if g["id"] == fav["game_id"]), None)
    if current_game:
        try:
            markets = current_game.get("bookmakers", [])[0].get("markets", [])
            h2h = next((m for m in markets if m["key"]=="h2h"), None)
            favorite_outcome = next(o for o in h2h["outcomes"] if o["name"] == fav["favorite_team"])
            current_odd = favorite_outcome["price"]
        except Exception:
            current_odd = None
    else:
        current_odd = None

    prev_odd = st.session_state.prev_odds.get(fav["game_id"], fav["initial_odd"])

    if current_odd and (current_odd - prev_odd) >= odd_increase_threshold:
        alerts.append(f"⚠️ Коефициент за {fav['favorite_team']} в мача {fav['match']} се покачи от {prev_odd:.2f} на {current_odd:.2f}!")
        if enable_sound:
            st.markdown("""
                <audio autoplay>
                    <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
                </audio>
            """, unsafe_allow_html=True)

    st.session_state.prev_odds[fav["game_id"]] = current_odd

    table_data.append({
        "Лига": fav["league"],
        "Мач": fav["match"],
        "Начален час": fav["commence_time"].strftime("%Y-%m-%d %H:%M"),
        "Фаворит": fav["favorite_team"],
        "Първоначален коефициент": fav["initial_odd"],
        "Актуален коефициент": current_odd
    })

df = pd.DataFrame(table_data)

st.dataframe(df, use_container_width=True)

if alerts:
    for alert in alerts:
        st.warning(alert)

st.write(f"Автоматично обновяване на всеки {refresh_interval} секунди...")
time.sleep(refresh_interval)
st.experimental_rerun()
