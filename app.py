import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime, timedelta

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

# ------------------- API Keys -------------------
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]

# Лиги (кодове за Football-Data API и Odds API трябва да съвпадат или да се коригират)
LEAGUES = {
    "Premier League": ("PL", "soccer_epl"),
    "La Liga": ("PD", "soccer_spain_la_liga"),
    "Bundesliga": ("BL1", "soccer_germany_bundesliga"),
    "Serie A": ("SA", "soccer_italy_serie_a"),
    "Ligue 1": ("FL1", "soccer_france_ligue_one"),
    "Champions League": ("CL", "soccer_uefa_champs_league")
}

# ------------------- Функции -------------------

# Вземаме коефициенти от Odds API
@st.cache_data(ttl=3600)
def get_odds_data(league_code_odds):
    url = f"https://api.the-odds-api.com/v4/sports/{league_code_odds}/odds"
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

# Вземаме класирането от Football-Data API
@st.cache_data(ttl=3600)
def get_standings(league_code_fd):
    url = f"https://api.football-data.org/v4/competitions/{league_code_fd}/standings"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return None
    data = res.json()
    return data.get("standings", [])

def get_team_stats(team_name, league_code_fd):
    standings = get_standings(league_code_fd)
    if not standings:
        return None
    for table in standings:
        for team in table.get("table", []):
            if team["team"]["name"].lower() == team_name.lower():
                stats = team
                played = stats["playedGames"]
                won = stats["won"]
                goal_diff = stats["goalDifference"]
                win_rate = won / played if played > 0 else 0
                return {
                    "win_rate": win_rate,
                    "goal_diff": goal_diff,
                    "played": played,
                    "position": stats["position"]
                }
    return None

def estimate_probabilities_from_stats(home_team, away_team, league_code_fd):
    home_stats = get_team_stats(home_team, league_code_fd)
    away_stats = get_team_stats(away_team, league_code_fd)
    if home_stats is None or away_stats is None:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}

    home_strength = home_stats["win_rate"] + 0.01 * home_stats["goal_diff"]
    away_strength = away_stats["win_rate"] + 0.01 * away_stats["goal_diff"]

    total = home_strength + away_strength
    if total == 0:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}

    p_home = home_strength / total
    p_away = away_strength / total
    p_draw = 1 - (p_home + p_away)
    p_draw = max(0, p_draw)

    total_prob = p_home + p_draw + p_away
    return {
        "home": p_home / total_prob,
        "draw": p_draw / total_prob,
        "away": p_away / total_prob
    }

# Извличаме мачове за следващите дни от Odds API
def get_upcoming_matches(days_ahead=3):
    today = datetime.utcnow()
    end_date = today + timedelta(days=days_ahead)
    upcoming = []

    for league_name, (league_code_fd, league_code_odds) in LEAGUES.items():
        matches = get_odds_data(league_code_odds)
        for game in matches:
            try:
                game_time = datetime.fromisoformat(game["commence_time"].replace("Z", ""))
                if today <= game_time <= end_date:
                    upcoming.append({
                        "league_fd": league_code_fd,
                        "league_odds": league_code_odds,
                        "league_name": league_name,
                        "match": f"{game['home_team']} vs {game['away_team']}",
                        "datetime": game_time,
                        "data": game
                    })
            except Exception:
                continue

    return sorted(upcoming, key=lambda x: x["datetime"])

# ------------------- UI -------------------
st.title("⚽ Value Bets Tracker with Real Stats")

# 1. Избор на лига
league_name = st.selectbox("Избери лига", list(LEAGUES.keys()))
league_code_fd, league_code_odds = LEAGUES[league_name]

# 2. Коефициенти за избраната лига
st.divider()
st.subheader(f"📡 Коефициенти: {league_name}")
odds_data = get_odds_data(league_code_odds)

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
                    for o in market["outcomes"]:
                        st.write(f"{o['name']}: {o['price']:.2f}")
else:
    st.info("Няма активни коефициенти за тази лига в момента.")

# 3. Мачове днес и следващите 3 дни с автоматично търсене на value bets
st.divider()
st.subheader("🗓️ Мачове за днес и следващите 3 дни с автоматично търсене на Value Bets")

upcoming = get_upcoming_matches(days_ahead=3)
value_bets_found = []

for item in upcoming:
    match = item["match"]
    league_fd = item["league_fd"]
    league_odds = item["league_odds"]
    home_team = item["data"]["home_team"]
    away_team = item["data"]["away_team"]

    probs = estimate_probabilities_from_stats(home_team, away_team, league_fd)

    h2h_odds = None
    for bookmaker in item["data"]["bookmakers"][:1]:
        for market in bookmaker["markets"]:
            if market["key"] == "h2h":
                h2h_odds = {o["name"]: o["price"] for o in market["outcomes"]}

    if not h2h_odds:
        continue

    for outcome_key, prob_key in zip(["home", "draw", "away"], ["home", "draw", "away"]):
        team_name = home_team if outcome_key == "home" else (away_team if outcome_key == "away" else "Draw")
        odd = h2h_odds.get(team_name)
        if odd:
            value = probs[prob_key] * odd - 1
            if value > 0.05:  # праг 5%
                bet_desc = f"{match} ({team_name})"
                # Проверяваме дали вече сме записали този залог
                existing = pd.read_sql("SELECT * FROM bets WHERE match = ? AND market = ? AND odds = ?", conn, params=(bet_desc, "1X2", odd))
                if existing.empty:
                    add_bet(
                        str(datetime.today().date()),
                        bet_desc,
                        "1X2",
                        odd,
                        stake=10,
                        status="open",
                        is_value_bet=1
                    )
                value_bets_found.append({
                    "Match": match,
                    "Outcome": team_name,
                    "Prob": f"{probs[prob_key]:.2f}",
                    "Odds": odd,
