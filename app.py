import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime
import matplotlib.pyplot as plt

FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
HISTORY_FILE = "bet_history.csv"

# ====== Лиги от Odds API ======
@st.cache_data(ttl=3600)
def get_supported_leagues():
    response = requests.get("https://api.the-odds-api.com/v4/sports", params={"apiKey": ODDS_API_KEY})
    data = response.json()
    return [sport for sport in data if sport["group"] == "Soccer"]

# ====== Odds API ======
@st.cache_data(ttl=3600)
def get_live_odds(sport_key):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
        )
        return response.json()
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

# ====== Football-Data API ======
@st.cache_data(ttl=3600)
def get_team_matches(team_id):
    try:
        res = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 100}
        )
        res.raise_for_status()
        return res.json()["matches"]
    except Exception:
        return []

TEAM_ID_MAPPING = {
    "Arsenal": 57, "Manchester City": 65, "Liverpool": 64, "Chelsea": 61,
    "Manchester United": 66, "Tottenham Hotspur": 73, "Newcastle United": 67,
    "Aston Villa": 58, "West Ham United": 563, "Brighton & Hove Albion": 397,
    "Wolverhampton Wanderers": 76, "Fulham": 63, "Crystal Palace": 354,
    "Everton": 62, "Brentford": 402, "Nottingham Forest": 351,
    "Bournemouth": 1044, "Burnley": 328, "Sheffield United": 356,
    "Luton Town": 389
}

def get_team_id(name):
    return TEAM_ID_MAPPING.get(name)

def get_stats(matches, team_name):
    goals, wins = [], 0
    for m in matches[:10]:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        score = m["score"]["fullTime"]
        is_home = home == team_name
        gf = score["home"] if is_home else score["away"]
        ga = score["away"] if is_home else score["home"]
        goals.append(gf)
        if gf > ga:
            wins += 1
    avg_goals = np.mean(goals) if goals else 1.0
    win_rate = wins / len(goals) if goals else 0.5
    return {"avg_goals": avg_goals, "win_rate": win_rate}

def format_date(iso):
    return datetime.fromisoformat(iso).strftime("%d %b %Y")

def calculate_poisson_probabilities(home_avg, away_avg):
    home_win, draw, away_win = 0, 0, 0
    for i in range(10):
        for j in range(10):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p
    total = home_win + draw + away_win
    return home_win/total, draw/total, away_win/total

def calculate_value_bets(prob, odds):
    return {
        'home': prob[0] - 1/odds['home'],
        'draw': prob[1] - 1/odds['draw'],
        'away': prob[2] - 1/odds['away']
    }

def plot_probabilities(title, labels, probs):
    fig, ax = plt.subplots()
    ax.bar(labels, probs, color=["#4CAF50", "#FFC107", "#2196F3"])
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_ylabel("Вероятност")
    st.pyplot(fig)

def save_history(match, prob, odds, values, chosen):
    row = {
        "datetime": datetime.now().isoformat(),
        "match": f"{match['home_team']} vs {match['away_team']}",
        "prob_home": prob[0],
        "prob_draw": prob[1],
        "prob_away": prob[2],
        "odds_home": odds["home"],
        "odds_draw": odds["draw"],
        "odds_away": odds["away"],
        "value_home": values["home"],
        "value_draw": values["draw"],
        "value_away": values["away"],
        "chosen_bet": chosen
    }
    df = pd.DataFrame([row])
    if os.path.exists(HISTORY_FILE):
        df.to_csv(HISTORY_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(HISTORY_FILE, index=False)

def display_history():
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        st.dataframe(df)
    else:
        st.info("Няма записана история.")

def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Advisor")

    leagues = get_supported_leagues()
    league_names = [l["title"] for l in leagues]
    selected_league = st.selectbox("Избери лига:", league_names)
    league_key = next(l["key"] for l in leagues if l["title"] == selected_league)

    matches = get_live_odds(league_key)
    if not matches:
        st.warning("Няма налични мачове.")
        return

    match_options = [f"{m['home_team']} vs {m['away_team']}" for m in matches]
    selected = st.selectbox("Избери мач:", match_options)
    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected)

    home_id = get_team_id(match["home_team"])
    away_id = get_team_id(match["away_team"])

    home_matches = get_team_matches(home_id) if home_id else []
    away_matches = get_team_matches(away_id) if away_id else []

    home_stats = get_stats(home_matches, match["home_team"])
    away_stats = get_stats(away_matches, match["away_team"])

    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
            "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
        }
    except Exception:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}

    prob = calculate_poisson_probabilities(home_stats["avg_goals"], away_stats["avg_goals"])
    values = calculate_value_bets(prob, best_odds)

    tab1, tab2, tab3 = st.tabs(["Анализ", "История на отборите", "История на залози"])

    with tab1:
        cols = st.columns(3)
        for col, (label, p, val, odd) in zip(cols, [
            (match["home_team"], prob[0], values["home"], best_odds["home"]),
            ("Равен", prob[1], values["draw"], best_odds["draw"]),
            (match["away_team"], prob[2], values["away"], best_odds["away"])
        ]):
            col.metric(label, f"{p*100:.1f}%", delta=f"Value: {val*100:.1f}%")
            col.write(f"Коефициент: {odd:.2f}")
        plot_probabilities("Поасон вероятности", [match["home_team"], "Равен", match["away_team"]], prob)
        choice = st.radio("Избери залог:", [match["home_team"], "Равен", match["away_team"]])
        if st.button("Запази залог"):
            save_history(match, prob, best_odds, values, choice)
            st.success("Залогът е запазен.")

    with tab2:
        st.subheader("Последни мачове")
        for team_name, matches in zip([match["home_team"], match["away_team"]], [home_matches, away_matches]):
            st.write(f"Последни 10 мача на **{team_name}**:")
            for m in matches[:10]:
                st.write(f"{format_date(m['utcDate'])} | {m['homeTeam']['name']} vs {m['awayTeam']['name']} | {m['score']['fullTime']['home']} - {m['score']['fullTime']['away']}")
        st.subheader("Директни мачове:")
        mutual = [m for m in home_matches if m["awayTeam"]["name"] == match["away_team"] or m["homeTeam"]["name"] == match["away_team"]]
        if mutual:
            for m in mutual[:10]:
                st.write(f"{format_date(m['utcDate'])} | {m['homeTeam']['name']} vs {m['awayTeam']['name']} | {m['score']['fullTime']['home']} - {m['score']['fullTime']['away']}")
        else:
            st.info("Няма намерени директни мачове.")

    with tab3:
        display_history()

if __name__ == "__main__":
    main()
