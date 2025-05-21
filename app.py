import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime
import os
import matplotlib.pyplot as plt

# ================ CONFIGURATION ================= #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Aston Villa": 58,
    "Brentford": 402,
    "Brighton & Hove Albion": 397,
    "Burnley": 328,
    "Chelsea": 61,
    "Crystal Palace": 354,
    "Everton": 62,
    "Fulham": 63,
    "Liverpool": 64,
    "Luton Town": 389,
    "Manchester City": 65,
    "Manchester United": 66,
    "Newcastle United": 67,
    "Nottingham Forest": 351,
    "Sheffield United": 356,
    "Tottenham Hotspur": 73,
    "West Ham United": 563,
    "Wolverhampton Wanderers": 76,
    "AFC Bournemouth": 1044
}

HISTORY_FILE = "bet_history.csv"

# ================ API FUNCTIONS ================= #

@st.cache_data(ttl=3600)
def get_all_leagues():
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error loading leagues: {str(e)}")
        return []

@st.cache_data(ttl=300)
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
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return []
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 10}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Stats Error for {team_name}: {str(e)}")
        return []

# ================ ANALYTICS FUNCTIONS =============== #
def calculate_poisson_probabilities(home_avg, away_avg):
    max_goals = 10
    home_win, draw, away_win = 0, 0, 0
    for i in range(max_goals):
        for j in range(max_goals):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p
    total = home_win + draw + away_win
    return home_win/total, draw/total, away_win/total

def calculate_value_bets(probabilities, odds):
    return {
        'home': probabilities[0] - 1/odds['home'],
        'draw': probabilities[1] - 1/odds['draw'],
        'away': probabilities[2] - 1/odds['away']
    }

# ================ UI HELPERS ======================= #
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, is_home=True):
    if not matches:
        return {"avg_goals": 1.2 if is_home else 0.9, "win_rate": 0.5 if is_home else 0.3}
    goals = []
    wins = 0
    for match in matches[-10:]:
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            opp_goals = match["score"]["fullTime"]["away"]
        else:
            team_goals = match["score"]["fullTime"]["away"]
            opp_goals = match["score"]["fullTime"]["home"]
        goals.append(team_goals)
        wins += 1 if team_goals > opp_goals else 0
    return {"avg_goals": np.mean(goals) if goals else 0, "win_rate": wins/len(matches[-10:])}

def plot_probabilities(title, labels, probabilities):
    fig, ax = plt.subplots()
    ax.bar(labels, probabilities, color=["#4CAF50", "#FFC107", "#2196F3"])
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_ylabel("Вероятност")
    st.pyplot(fig)

# ================ HISTORY MANAGEMENT =============== #
def save_history(match, probabilities, odds, values, chosen):
    row = {
        "datetime": datetime.now().isoformat(),
        "match": f"{match['home_team']} vs {match['away_team']}",
        "prob_home": probabilities[0],
        "prob_draw": probabilities[1],
        "prob_away": probabilities[2],
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
        st.info("Все още няма записана история.")

# ================ MAIN APP ========================= #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    # Зареждаме всички лиги от API и филтрираме само футболни
    leagues = get_all_leagues()
    league_options = {l["key"]: f"{l.get('group', '')} - {l['title']}".strip(" -") for l in leagues if "soccer" in l["key"]}
    if not league_options:
        st.error("Неуспешно зареждане на първенства.")
        return

    selected_league = st.selectbox("Изберете първенство:", options=list(league_options.keys()), format_func=lambda x: league_options[x])

    with st.spinner(f"Зареждане на live коефициенти за {league_options[selected_league]}..."):
        matches = get_live_odds(selected_league)

    if not matches:
        st.warning("Няма налични мачове в момента.")
        return

    match_options = [f"{m['home_team']} vs {m['away_team']}" for m in matches]
    selected_match = st.selectbox("Изберете мач:", match_options)

    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)

    with st.spinner("Анализ на отборите..."):
        home_matches = get_team_stats(match["home_team"])
        away_matches = get_team_stats(match["away_team"])

        home_stats = get_team_stats_data(home_matches, is_home=True)
        away_stats = get_team_stats_data(away_matches, is_home=False)

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

    tab1, tab2 = st.tabs(["Анализ на мача", "История на залозите"])

    with tab1:
        cols = st.columns(3)
        outcomes = [
            (match['home_team'], prob[0], values["home"], best_odds["home"]),
            ("Равен", prob[1], values["draw"], best_odds["draw"]),
            (match['away_team'], prob[2], values["away"], best_odds["away"])
        ]
        for col, (label, prob_val, val, odd) in zip(cols, outcomes):
            col.markdown(f"### {label}")
            col.markdown(f"Вероятност: {prob_val:.2%}")
            col.markdown(f"Стойност: {val:.3f}")
            col.markdown(f"Коефициент: {odd}")

        chosen = st.radio("Изберете залог за запазване:", [o[0] for o in outcomes])

        if st.button("Запази залог"):
            save_history(match, prob, best_odds, values, chosen)
            st.success(f"Залог '{chosen}' запазен успешно!")

    with tab2:
        display_history()

if __name__ == "__main__":
    main()
