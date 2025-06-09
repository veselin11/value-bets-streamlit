import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime, timedelta
import pytz
import toml

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

def add_bet(date, match, market, odds, stake, status="open", is_value_bet=0):
    c.execute("INSERT INTO bets (date, match, market, odds, stake, status, is_value_bet) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (date, match, market, odds, stake, status, is_value_bet))
    conn.commit()

def get_bets():
    return pd.read_sql("SELECT * FROM bets", conn)

# ------------------- API -------------------
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

@st.cache_data(ttl=300)
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

# ------------------- UI -------------------
st.title("⚽ Value Bets Tracker")

# 1. Меню за избор на лига
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

# 3. Следене на фаворити на живо
st.divider()
st.subheader("🎯 Следене на фаворити с покачване на коефициент")

FAVORITE_THRESHOLD = 1.50
ALERT_INCREASE = 0.20

all_fav_matches = []
for league in LEAGUES.values():
    matches = get_odds_data(league)
    for game in matches:
        try:
            home = game["home_team"]
            away = game["away_team"]
            match_id = game["id"]
            commence = datetime.fromisoformat(game["commence_time"].replace("Z", ""))
            today = datetime.utcnow()
            if commence.date() != today.date():
                continue

            for bookmaker in game["bookmakers"][:1]:
                for market in bookmaker["markets"]:
                    if market["key"] == "h2h":
                        outcomes = market["outcomes"]
                        odds = {o["name"]: o["price"] for o in outcomes}
                        min_odd = min(odds.values())
                        favorite = min(odds, key=odds.get)
                        if min_odd <= FAVORITE_THRESHOLD:
                            game_info = {
                                "match": f"{home} vs {away}",
                                "start_time": commence.strftime("%H:%M"),
                                "favorite": favorite,
                                "start_odd": min_odd,
                                "current_odd": min_odd,
                                "alert": False
                            }

                            if "last_odds" not in st.session_state:
                                st.session_state.last_odds = {}

                            prev_odd = st.session_state.last_odds.get(match_id, min_odd)
                            st.session_state.last_odds[match_id] = min_odd

                            if min_odd - prev_odd >= ALERT_INCREASE:
                                game_info["alert"] = True

                            all_fav_matches.append(game_info)
        except:
            continue

if all_fav_matches:
    df = pd.DataFrame(all_fav_matches)
    for _, row in df.iterrows():
        alert_color = "red" if row.alert else "black"
        st.markdown(f"<span style='color:{alert_color};font-size:18px'>⚽ {row['match']} ({row['start_time']}) — 📈 {row['favorite']} @ {row['current_odd']:.2f}</span>", unsafe_allow_html=True)
        if row.alert:
            st.warning(f"🚨 Повишен коефициент за фаворита {row['favorite']}!")
else:
    st.info("Няма мачове с фаворити или промени в коефициентите днес.")

# 4. Таблица със залози
st.divider()
st.subheader("📋 Моите залози")
bets_df = get_bets()
st.dataframe(bets_df, use_container_width=True)
                        
