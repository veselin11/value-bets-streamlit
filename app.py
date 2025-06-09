import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

# --- Конфигурация ---
API_KEY = st.secrets["ODDS_API_KEY"]
LEAGUES = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
    "Serie A": "soccer_italy_serie_a",
    "Ligue 1": "soccer_france_ligue_one",
    "Champions League": "soccer_uefa_champs_league"
}

# --- Функция за взимане на коефициенти ---
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

# --- Функция за филтриране на фаворити ---
def filter_favorites(games, threshold=1.5):
    """Връща списък от мачове, където фаворитът има коефициент под threshold"""
    filtered = []
    for game in games:
        try:
            markets = game.get("bookmakers", [])[0].get("markets", [])
            h2h = next((m for m in markets if m["key"]=="h2h"), None)
            if not h2h:
                continue
            odds_list = [o["price"] for o in h2h["outcomes"]]
            min_odd = min(odds_list)
            if min_odd <= threshold:
                favorite = min(h2h["outcomes"], key=lambda x: x["price"])
                filtered.append({
                    "league": game["sport_title"],
                    "match": f"{game['home_team']} vs {game['away_team']}",
                    "commence_time": datetime.fromisoformat(game["commence_time"].replace("Z","")),
                    "favorite_team": favorite["name"],
                    "initial_odd": favorite["price"],
                    "game_id": game["id"]
                })
        except Exception as e:
            # Ако има грешка при данните, игнорирай този мач
            continue
    # Сортиране по начален час
    filtered.sort(key=lambda x: x["commence_time"])
    return filtered

# --- Основен UI ---
st.title("Live Фаворити и Коефициенти ⚽")

# Sidebar настройки
st.sidebar.header("Настройки на сигнала")
odd_increase_threshold = st.sidebar.slider("Минимално покачване за сигнал", 0.05, 1.0, 0.2, 0.05)
refresh_interval = st.sidebar.slider("Интервал за обновяване (сек.)", 30, 600, 300, 30)
enable_sound = st.sidebar.checkbox("Включи звуков сигнал при промяна", value=True)

# Избор на лига
selected_league_name = st.sidebar.selectbox("Избери лига", list(LEAGUES.keys()))
selected_league_code = LEAGUES[selected_league_name]

# Зареждане на мачове
all_games = fetch_odds(selected_league_code)
favorites = filter_favorites(all_games, threshold=1.5)

# Съхраняваме предишните коефициенти в сесия
if "prev_odds" not in st.session_state:
    st.session_state.prev_odds = {}

# Таблица за показване
table_data = []
alerts = []

for fav in favorites:
    # Взимаме текущи коефициенти за този мач
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

    # Вземаме стария коефициент за сравнение
    prev_odd = st.session_state.prev_odds.get(fav["game_id"], fav["initial_odd"])

    # Проверяваме дали има значимо покачване
    if current_odd and (current_odd - prev_odd) >= odd_increase_threshold:
        alerts.append(f"⚠️ Коефициент за {fav['favorite_team']} в мача {fav['match']} се покачи от {prev_odd:.2f} на {current_odd:.2f}!")

        # Може да добавиш звуков сигнал с JS или HTML, но Streamlit има ограничения
        if enable_sound:
            st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg", format="audio/ogg")

    # Запазваме текущия коефициент
    st.session_state.prev_odds[fav["game_id"]] = current_odd

    table_data.append({
        "Лига": fav["league"],
        "Мач": fav["match"],
        "Начален час": fav["commence_time"].strftime("%Y-%m-%d %H:%M"),
        "Фаворит": fav["favorite_team"],
        "Първоначален коефициент": fav["initial_odd"],
        "Актуален коефициент": current_odd
    })

# Показваме таблицата
df = pd.DataFrame(table_data)
st.dataframe(df, use_container_width=True)

# Показваме алармите
if alerts:
    for alert in alerts:
        st.warning(alert)

# Автоматично опресняване
st.write(f"Автоматично обновяване на данните на всеки {refresh_interval} секунди...")
time.sleep(refresh_interval)
st.experimental_rerun()
