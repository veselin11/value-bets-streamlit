import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime, timedelta
import pytz

# ------------------- DB -------------------
DB_PATH = "bets.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    match TEXT,
    market TEXT,
    odds REAL,
    stake REAL,
    status TEXT,
    is_value_bet INTEGER
)''')
conn.commit()

# ------------------- DB функции -------------------
def add_bet(date, match, market, odds, stake, status="open", is_value_bet=0):
    c.execute("INSERT INTO bets (date, match, market, odds, stake, status, is_value_bet) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (date, match, market, odds, stake, status, is_value_bet))
    conn.commit()

def get_bets():
    return pd.read_sql("SELECT * FROM bets", conn)

# ------------------- API -------------------
import toml
secrets = toml.load(".streamlit/secrets.toml")
ODDS_API_KEY = secrets["ODDS_API_KEY"]

LEAGUES = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
    "Serie A": "soccer_italy_serie_a",
    "Ligue 1": "soccer_france_ligue_one",
    "Champions League": "soccer_uefa_champs_league"
}

@st.cache_data(ttl=3600)
def get_odds_data(league="soccer_epl"):
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        return res.json()
    else:
        return []

def get_upcoming_matches(days_ahead=3):
    all_leagues = list(LEAGUES.values())
    today = datetime.utcnow()
    end_date = today + timedelta(days=days_ahead)
    upcoming = []

    for league in all_leagues:
        matches = get_odds_data(league=league)
        for game in matches:
            try:
                game_time = datetime.fromisoformat(game["commence_time"].replace("Z", ""))
                if today <= game_time <= end_date:
                    upcoming.append({
                        "league": league,
                        "match": f"{game['home_team']} vs {game['away_team']}",
                        "datetime": game_time,
                        "data": game
                    })
            except Exception:
                continue

    return sorted(upcoming, key=lambda x: x["datetime"])

# ------------------- UI -------------------
st.title("⚽ Value Bets Tracker")

# 1. Избор на лига
league_name = st.selectbox("Избери лига", list(LEAGUES.keys()))
league_code = LEAGUES[league_name]

# 2. Показване на коефициенти от избраната лига
st.divider()
st.subheader(f"📡 Коефициенти: {league_name}")
odds_data = get_odds_data(league=league_code)

if odds_data:
    for game in odds_data[:5]:
        home = game["home_team"]
        away = game["away_team"]
        commence = game["commence_time"].replace("T", " ").replace("Z", "")
        match_str = f"{home} vs {away}"
        st.markdown(f"### {match_str} — 🕒 {commence}")

        for bookmaker in game["bookmakers"][:1]:
            st.markdown(f"**📌 Букмейкър:** {bookmaker['title']}")
            for market in bookmaker["markets"]:
                if market["key"] == "h2h":
                    outcomes = market["outcomes"]
                    for o in outcomes:
                        st.write(f"{o['name']}: {o['price']:.2f}")
else:
    st.info("Няма активни коефициенти за тази лига в момента.")

# 3. Актуални мачове до 3 дни напред
st.divider()
st.subheader("🗓️ Мачове за днес и следващите 3 дни")
upcoming = get_upcoming_matches()

if upcoming:
    for item in upcoming:
        match = item["match"]
        date_str = item["datetime"].strftime("%Y-%m-%d %H:%M")
        game = item["data"]
        st.markdown(f"### {match} — 🕒 {date_str} ({item['league']})")

        for bookmaker in game["bookmakers"][:1]:
            for market in bookmaker["markets"]:
                if market["key"] == "h2h":
                    outcomes = market["outcomes"]
                    for o in outcomes:
                        st.write(f"{o['name']}: {o['price']:.2f}")

                    with st.expander("🎯 Провери и запиши Value Bet"):
                        selected_team = st.selectbox("Отбор", [o["name"] for o in outcomes], key=game["id"])
                        your_prob = st.number_input("Твоя вероятност (%)", min_value=1.0, max_value=100.0, step=0.1, key="prob_" + game["id"])
                        stake = st.number_input("Заложена сума", min_value=0.1, step=0.1, value=10.0, key="stake_" + game["id"])

                        if st.button("Запиши Value Bet", key="btn_" + game["id"]):
                            selected_odds = next((o["price"] for o in outcomes if o["name"] == selected_team), None)
                            value = (your_prob / 100) * selected_odds - 1
                            if value > 0:
                                add_bet(
                                    str(datetime.today().date()),
                                    f"{match} ({selected_team})",
                                    "1X2",
                                    selected_odds,
                                    stake,
                                    status="open",
                                    is_value_bet=1
                                )
                                st.success(f"✅ Записан е Value Bet със стойност {value * 100:.2f}%")
                            else:
                                st.warning(f"❌ Няма стойност. Value = {value * 100:.2f}%")
else:
    st.info("Няма мачове в следващите дни с налични коефициенти.")

# 4. Таблица със залози
st.divider()
st.subheader("📋 Моите залози")
bets_df = get_bets()
st.dataframe(bets_df, use_container_width=True)
