import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

# ================== GLOBALS ================== #
SPORTS = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one"
}

# ================== CACHING ================== #
@st.cache_data(ttl=3600)
def get_live_odds(league_key):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{league_key}/odds",
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
def get_team_stats(team_id):
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 10}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Stats Error: {str(e)}")
        return []

@st.cache_data
def load_ml_artifacts():
    try:
        return (
            joblib.load("model.pkl"),
            joblib.load("scaler.pkl")
        )
    except:
        return None, None

# ================== ANALYTICS ================== #
def calculate_poisson_probabilities(home_avg, away_avg):
    max_goals = 10
    home_win = draw = away_win = 0
    for i in range(max_goals):
        for j in range(max_goals):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p
    return home_win, draw, away_win

def calculate_value_bets(probabilities, odds):
    return {
        "home": probabilities[0] - 1/odds["home"],
        "draw": probabilities[1] - 1/odds["draw"],
        "away": probabilities[2] - 1/odds["away"]
    }

def predict_with_ai(home_stats, away_stats):
    model, scaler = load_ml_artifacts()
    if model is None:
        return None
    features = np.array([
        home_stats["avg_goals"],
        away_stats["avg_goals"],
        home_stats["win_rate"],
        away_stats["win_rate"]
    ]).reshape(1, -1)
    return model.predict_proba(scaler.transform(features))[0]

# ================== HELPERS ================== #
def format_date(date_str):
    return datetime.fromisoformat(date_str).strftime("%d %b %Y")

def get_stats_from_matches(matches, team_name):
    goals = []
    wins = 0
    for match in matches:
        if match['homeTeam']['name'] == team_name:
            scored = match['score']['fullTime']['home']
            conceded = match['score']['fullTime']['away']
            result = "Win" if scored > conceded else ("Draw" if scored == conceded else "Loss")
        else:
            scored = match['score']['fullTime']['away']
            conceded = match['score']['fullTime']['home']
            result = "Win" if scored > conceded else ("Draw" if scored == conceded else "Loss")

        goals.append(scored)
        if result == "Win":
            wins += 1
    return {
        "avg_goals": np.mean(goals) if goals else 1,
        "win_rate": wins / len(matches) if matches else 0
    }

# ================== MAIN ================== #
def main():
    st.set_page_config(layout="wide")
    st.title("⚽ Smart Betting Advisor")

    selected_league = st.selectbox("Избери първенство:", list(SPORTS.keys()))
    matches = get_live_odds(SPORTS[selected_league])

    if not matches:
        st.warning("Няма активни срещи.")
        return

    st.subheader("Налични срещи")
    match_buttons = []
    for idx, match in enumerate(matches):
        date = datetime.fromisoformat(match["commence_time"]).strftime("%d %b %Y %H:%M")
        if st.button(f"{match['home_team']} vs {match['away_team']} | {date}", key=idx):
            st.session_state.selected_match = idx

    selected_match_index = st.session_state.get("selected_match")
    if selected_match_index is None:
        st.info("Избери среща за анализ.")
        return

    match = matches[selected_match_index]
    home_team = match["home_team"]
    away_team = match["away_team"]
    home_id = None
    away_id = None

    # Match Analysis
    tab1, tab2, tab3, tab4 = st.tabs([
        "Прогноза", "История на отбори", "AI прогноза", "История на залози"
    ])

    with tab1:
        st.subheader("Анализ на мача")
        home_stats = get_stats_from_matches(get_team_stats(home_id or 64), home_team)
        away_stats = get_stats_from_matches(get_team_stats(away_id or 66), away_team)

        try:
            best_odds = {
                "home": max(o["price"] for b in match["bookmakers"] 
                            for o in b["markets"][0]["outcomes"] if o["name"] == home_team),
                "draw": max(o["price"] for b in match["bookmakers"] 
                            for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
                "away": max(o["price"] for b in match["bookmakers"] 
                            for o in b["markets"][0]["outcomes"] if o["name"] == away_team)
            }
        except:
            best_odds = {"home": 1.8, "draw": 3.5, "away": 4.2}

        prob = calculate_poisson_probabilities(home_stats["avg_goals"], away_stats["avg_goals"])
        values = calculate_value_bets(prob, best_odds)

        cols = st.columns(3)
        for col, label, p, v, odd in zip(cols,
                                         [f"Победа {home_team}", "Равен", f"Победа {away_team}"],
                                         prob, [values["home"], values["draw"], values["away"]],
                                         [best_odds["home"], best_odds["draw"], best_odds["away"]]):
            with col:
                st.metric(label="Вероятност", value=f"{p*100:.1f}%")
                st.metric(label="Коефициент", value=f"{odd:.2f}")
                st.markdown(f"**Стойност:** {'+' if v > 0 else ''}{v*100:.1f}%")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"{home_team} - последни мачове")
            for match in get_team_stats(home_id or 64):
                opponent = match['awayTeam']['name'] if match['homeTeam']['name'] == home_team else match['homeTeam']['name']
                score = match['score']['fullTime']
                result = f"{score['home']} - {score['away']}"
                date = format_date(match['utcDate'])
                st.caption(f"{date} vs {opponent} | {result}")

        with col2:
            st.subheader(f"{away_team} - последни мачове")
            for match in get_team_stats(away_id or 66):
                opponent = match['awayTeam']['name'] if match['homeTeam']['name'] == away_team else match['homeTeam']['name']
                score = match['score']['fullTime']
                result = f"{score['away']} - {score['home']}"
                date = format_date(match['utcDate'])
                st.caption(f"{date} vs {opponent} | {result}")

    with tab3:
        if st.button("Изчисли AI прогноза"):
            prediction = predict_with_ai(home_stats, away_stats)
            if prediction is not None:
                st.subheader("Резултат от AI модела")
                for label, p in zip([f"Победа {home_team}", "Равен", f"Победа {away_team}"], prediction):
                    st.markdown(f"**{label}**: {p*100:.1f}%")

    with tab4:
        st.subheader("История на залозите")
        st.write("Тук ще се визуализира история на направени залози (в процес на интеграция)...")

if __name__ == "__main__":
    main()
    
