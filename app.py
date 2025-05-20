import streamlit as st
import requests
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
SPORT = "soccer"  # Взимаме всички футболни събития

TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Aston Villa": 58,
    "Brentford": 402,
    "Brighton": 397,
    "Burnley": 328,
    "Chelsea": 61,
    "Crystal Palace": 354,
    "Everton": 62,
    "Fulham": 63,
    "Liverpool": 64,
    "Luton": 389,
    "Manchester City": 65,
    "Manchester United": 66,
    "Newcastle United": 67,
    "Nottingham Forest": 351,
    "Sheffield United": 356,
    "Tottenham": 73,
    "West Ham": 563,
    "Wolves": 76,
    "Bournemouth": 1044
}

# ================== API FUNCTIONS ================== #
@st.cache_data(ttl=3600)
def get_live_odds():
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
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
def get_team_matches(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return []
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 30}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Error getting matches for {team_name}: {str(e)}")
        return []

# ================== DATA PROCESSING ================== #
def process_matches(matches, team_name, is_home=True):
    filtered = [m for m in matches if (
        m["homeTeam"]["name"] == team_name if is_home else m["awayTeam"]["name"] == team_name
    )]
    recent = filtered[-10:] if len(filtered) >= 10 else filtered
    goals = []
    wins = 0
    for match in recent:
        team_goals = match["score"]["fullTime"]["home"] if is_home else match["score"]["fullTime"]["away"]
        opponent_goals = match["score"]["fullTime"]["away"] if is_home else match["score"]["fullTime"]["home"]
        goals.append(team_goals)
        if team_goals > opponent_goals:
            wins += 1
    return {
        "avg_goals": np.mean(goals) if goals else 0,
        "win_rate": wins / len(recent) if recent else 0
    }

def calculate_poisson(home_avg, away_avg):
    max_goals = 6
    home_prob, draw_prob, away_prob = 0, 0, 0
    for i in range(max_goals):
        for j in range(max_goals):
            prob = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_prob += prob
            elif i == j:
                draw_prob += prob
            else:
                away_prob += prob
    total = home_prob + draw_prob + away_prob
    return home_prob / total, draw_prob / total, away_prob / total

def format_date(iso_str):
    return datetime.fromisoformat(iso_str.replace("Z", "")).strftime("%d/%m/%Y")

# ================== MAIN UI ================== #
def main():
    st.set_page_config(page_title="Football Analyzer", layout="wide")
    st.title("Football Match Analyzer")

    matches = get_live_odds()
    if not matches:
        st.warning("No live matches available.")
        return

    match_names = [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    selected = st.selectbox("Select a match", match_names)
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected)

    home_team = match["home_team"]
    away_team = match["away_team"]

    with st.spinner("Analyzing teams..."):
        home_matches = get_team_matches(home_team)
        away_matches = get_team_matches(away_team)
        home_stats = process_matches(home_matches, home_team, is_home=True) if home_matches else {"avg_goals": 0, "win_rate": 0}
        away_stats = process_matches(away_matches, away_team, is_home=False) if away_matches else {"avg_goals": 0, "win_rate": 0}

    best_odds = {"home": 1.0, "draw": 1.0, "away": 1.0}
    for bookmaker in match.get("bookmakers", []):
        for outcome in bookmaker.get("markets", [])[0].get("outcomes", []):
            if outcome["name"] == home_team:
                best_odds["home"] = max(best_odds["home"], outcome["price"])
            elif outcome["name"] == "Draw":
                best_odds["draw"] = max(best_odds["draw"], outcome["price"])
            elif outcome["name"] == away_team:
                best_odds["away"] = max(best_odds["away"], outcome["price"])

    home_prob, draw_prob, away_prob = calculate_poisson(home_stats["avg_goals"], away_stats["avg_goals"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(f"🏠 {home_team}")
        st.metric("Avg Goals", f"{home_stats['avg_goals']:.1f}")
        st.metric("Win Rate", f"{home_stats['win_rate']:.0%}")
        st.metric("Probability", f"{home_prob:.1%}")
        st.metric("Odds", f"{best_odds['home']:.2f}")
    with col2:
        st.subheader("⚖ Draw")
        st.metric("Probability", f"{draw_prob:.1%}")
        st.metric("Odds", f"{best_odds['draw']:.2f}")
    with col3:
        st.subheader(f"✈ {away_team}")
        st.metric("Avg Goals", f"{away_stats['avg_goals']:.1f}")
        st.metric("Win Rate", f"{away_stats['win_rate']:.0%}")
        st.metric("Probability", f"{away_prob:.1%}")
        st.metric("Odds", f"{best_odds['away']:.2f}")

    st.subheader("Recent Matches")
    col4, col5 = st.columns(2)
    with col4:
        if home_matches:
            st.caption(f"Last {len(home_matches[-5:])} home matches - {home_team}")
            for m in reversed(home_matches[-5:]):
                if m["homeTeam"]["name"] == home_team:
                    score = f"{m['score']['fullTime']['home']}-{m['score']['fullTime']['away']}"
                    st.write(f"{format_date(m['utcDate'])} | {score}")
    with col5:
        if away_matches:
            st.caption(f"Last {len(away_matches[-5:])} away matches - {away_team}")
            for m in reversed(away_matches[-5:]):
                if m["awayTeam"]["name"] == away_team:
                    score = f"{m['score']['fullTime']['away']}-{m['score']['fullTime']['home']}"
                    st.write(f"{format_date(m['utcDate'])} | {score}")

if __name__ == "__main__":
    main()
