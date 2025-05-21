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

# ================== CONFIGURATION ================== #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
SPORT = "soccer_epl"

# Добавени всички налични първенства от The Odds API
LEAGUES = {
    "English Premier League": "soccer_epl",
    "Spanish La Liga": "soccer_spain_la_liga",
    "German Bundesliga": "soccer_germany_bundesliga",
    "Italian Serie A": "soccer_italy_serie_a",
    "French Ligue 1": "soccer_france_ligue_one",
    "UEFA Champions League": "soccer_uefa_champs_league",
    "UEFA Europa League": "soccer_uefa_europa_league",
    "Dutch Eredivisie": "soccer_netherlands_eredivisie",
    "Portuguese Primeira Liga": "soccer_portugal_primeira_liga",
    "Russian Premier League": "soccer_russia_premier_league",
    # Можеш да добавиш още от https://the-odds-api.com/sports
}

# Примерен речник за мапинг на отбори, може да го разширяваш по същия начин
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

# ================== API FUNCTIONS ================== #
@st.cache_data(ttl=3600)
def get_live_odds(sport_code):
    """Fetch real-time odds from The Odds API"""
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_code}/odds",
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
    """Fetch team match data from Football-Data.org"""
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return None
    
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

# ================== ANALYTICS FUNCTIONS ================== #
def calculate_poisson_probabilities(home_avg, away_avg):
    max_goals = 10
    home_win, draw, away_win = 0, 0, 0
    
    for i in range(max_goals):
        for j in range(max_goals):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j: home_win += p
            elif i == j: draw += p
            else: away_win += p
    
    total = home_win + draw + away_win
    return home_win/total, draw/total, away_win/total

def calculate_value_bets(probabilities, odds):
    return {
        'home': probabilities[0] - 1/odds['home'],
        'draw': probabilities[1] - 1/odds['draw'],
        'away': probabilities[2] - 1/odds['away']
    }

# ================== ML FUNCTIONS ================== #
def load_ml_artifacts():
    try:
        return (
            joblib.load("model.pkl"),
            joblib.load("scaler.pkl")
        )
    except FileNotFoundError:
        st.error("ML artifacts missing! Please train model first")
        return None, None

def predict_with_ai(home_stats, away_stats):
    model, scaler = load_ml_artifacts()
    if not model: return None
    
    features = np.array([
        home_stats["avg_goals"],
        away_stats["avg_goals"],
        home_stats["win_rate"],
        away_stats["win_rate"]
    ]).reshape(1, -1)
    
    return model.predict_proba(scaler.transform(features))[0]

# ================== UI HELPER FUNCTIONS ================== #
def format_date(iso_date):
    return datetime.fromisoformat(iso_date).strftime("%d %b %Y")

def get_team_stats_data(matches, is_home=True):
    if not matches:
        return {
            "avg_goals": 1.2 if is_home else 0.9,
            "win_rate": 0.5 if is_home else 0.3
        }
    
    goals = []
    wins = 0
    
    for match in matches[-10:]:
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            opp_goals = match["score"]["fullTime"]["away"]
            opponent = match["awayTeam"]["name"]
            is_winner = team_goals > opp_goals
        else:
            team_goals = match["score"]["fullTime"]["away"]
            opp_goals = match["score"]["fullTime"]["home"]
            opponent = match["homeTeam"]["name"]
            is_winner = team_goals > opp_goals
        
        goals.append(team_goals)
        wins += 1 if is_winner else 0
    
    return {
        "avg_goals": np.mean(goals) if goals else 0,
        "win_rate": wins/len(matches[-10:]) if matches else 0
    }

def show_match_history(matches, is_home=True):
    if not matches:
        st.write("No recent matches found")
        return
    for match in reversed(matches[-10:]):
        if is_home:
            team_goals = match["score"]["fullTime"]["home"]
            opp_goals = match["score"]["fullTime"]["away"]
            opponent = match["awayTeam"]["name"]
            result = "W" if team_goals > opp_goals else "L" if team_goals < opp_goals else "D"
            score_str = f"{team_goals}-{opp_goals}"
        else:
            team_goals = match["score"]["fullTime"]["away"]
            opp_goals = match["score"]["fullTime"]["home"]
            opponent = match["homeTeam"]["name"]
            result = "W" if team_goals > opp_goals else "L" if team_goals < opp_goals else "D"
            score_str = f"{team_goals}-{opp_goals}"
        
        st.caption(f"{format_date(match['utcDate'])} | vs {opponent} | {score_str} | {result}")

@st.cache_data(ttl=3600)
def get_upcoming_matches(sport_code):
    """Get upcoming matches for selected league"""
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_code}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal"
            }
        )
        response.raise_for_status()
        matches = response.json()
        # Филтрирай само предстоящи (future) - ако съществува статус
        # Ако няма, ще покажем всички, защото са live odds
        return matches
    except Exception as e:
        st.error(f"Error fetching upcoming matches: {e}")
        return []

# ================== MAIN INTERFACE ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    # Избор на първенство
    league_name = st.selectbox("Избери първенство:", list(LEAGUES.keys()))
    sport_code = LEAGUES[league_name]

    with st.spinner("Зареждане на live коефициенти..."):
        matches = get_live_odds(sport_code)
    
    if not matches:
        st.warning("Няма налични мачове")
        return

    # Показване на предстоящи мачове
    st.subheader("Предстоящи мачове")
    upcoming_matches = matches[:10]  # Ограничаваме до 10 мача за по-добър UI
    for m in upcoming_matches:
        st.write(f"{m['commence_time'][:10]} | {m['home_team']} vs {m['away_team']}")

    # Избор на мач за анализ
    selected_match = st.selectbox(
        "Избери мач за анализ:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches],
        index=0
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match)

    with st.spinner("Анализ на отборите..."):
        home_matches = get_team_stats(match["home_team"])
        away_matches = get_team_stats(match["away_team"])
        home_stats = get_team_stats_data(home_matches, is_home=True)
        away_stats = get_team_stats_data(away_matches, is_home=False)

    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] 
                       for o in b["markets"][0]["outcomes"] 
                       if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] 
                       for o in b["markets"][0]["outcomes"] 
                       if o["name"] == "Draw"),
            "away": max(o["price"] for b in match["bookmakers"] 
                       for o in b["markets"][0]["outcomes"] 
                       if o["name"] == match["away_team"])
        }
    except:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], 
        away_stats["avg_goals"]
    )

    value_bets = calculate_value_bets(
        (prob_home, prob_draw, prob_away),
        best_odds
    )

    tab1, tab2, tab3 = st.tabs(["Match Analysis", "Team History", "AI Predictions"])

    with tab1:
        cols = st.columns(3)
        outcomes = [
            ("🏠 Домакин Победа", prob_home, value_bets["home"], best_odds["home"]),
            ("⚖ Равен", prob_draw, value_bets["draw"], best_odds["draw"]),
            ("✈ Гост Победа", prob_away, value_bets["away"], best_odds["away"])
        ]
        for col, (title, prob, value, odds) in zip(cols, outcomes):
            with col:
                st.subheader(title)
                st.metric("Вероятност", f"{prob*100:.1f}%")
                st.metric("Най-добър коефициент", f"{odds:.2f}")
                value_color = "green" if value > 0 else "red"
                st.markdown(f"**Value:** <span style='color:{value_color}'>{(value*100):.1f}%</span>", unsafe_allow_html=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Последни 10 мача - {match['home_team']}")
            show_match_history(home_matches, is_home=True)
        with col2:
            st.subheader(f"Последни 10 мача - {match['away_team']}")
            show_match_history(away_matches, is_home=False)

    with tab3:
        if st.button("Генерирай AI прогноза"):
            with st.spinner("Анализиране..."):
                prediction = predict_with_ai(home_stats, away_stats)
            if prediction is not None:
                st.subheader("🤖 Резултати от AI прогнозата")
                cols = st.columns(3)
                labels = ["Домакин Победа", "Равен", "Гост Победа"]
                colors = ["#4CAF50", "#FFC107", "#2196F3"]
                for col, label, prob, color in zip(cols, labels, prediction, colors):
                    with col:
                        st.markdown(f"<h3 style='color:{color}'>{label}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<h2>{prob*100:.1f}%</h2>", unsafe_allow_html=True)
            else:
                st.warning("AI прогноза не е налична.")

if __name__ == "__main__":
    main()
