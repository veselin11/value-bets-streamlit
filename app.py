import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os

# ================ CONFIGURATION ================= #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

LANGUAGES = {
    "Български": {
        "select_league": "Избери първенство:",
        "select_match": "Изберете мач:",
        "value": "Стойност",
        "odds": "Коефициент",
        "no_matches": "Няма налични мачове.",
        "settings": "Настройки",
        "min_odds": "Минимален коефициент",
        "predictions": "Прогнози",
        "history": "История",
        "live": "На живо",
        "bet_history": "История на залозите",
        "refresh_history": "Обнови историята",
        "no_history": "Все още няма записани залози.",
        "live_updates": "Обновления на живо",
        "refresh": "Обнови",
        "kelly_title": "Кели Калкулатор",
        "bankroll": "Бюджет",
        "confidence": "Увереност (%)",
        "max_stake": "Макс. залог (%)",
        "avg_goals": "Средни голове",
        "conceded": "Получени",
        "last_5": "Последни 5 мача",
        "home": "Домакин",
        "away": "Гост",
        "points": "точки",
        "select_team": "Избери отбор (търсене)",
        "place_bet": "Постави залог",
        "stake": "Залог (в единици)",
        "bet_success": "Залогът беше записан успешно!",
        "invalid_stake": "Моля, въведете валидна стойност за залога.",
        "kelly_recommendation": "Препоръчан залог по Кели:",
    },
    "English": {
        "select_league": "Select league:",
        "select_match": "Select match:",
        "value": "Value",
        "odds": "Odds",
        "no_matches": "No matches available.",
        "settings": "Settings",
        "min_odds": "Minimum odds",
        "predictions": "Predictions",
        "history": "History",
        "live": "Live",
        "bet_history": "Bet History",
        "refresh_history": "Refresh History",
        "no_history": "No bets placed yet.",
        "live_updates": "Live Updates",
        "refresh": "Refresh",
        "kelly_title": "Kelly Calculator",
        "bankroll": "Bankroll",
        "confidence": "Confidence (%)",
        "max_stake": "Max Stake (%)",
        "avg_goals": "Avg Goals",
        "conceded": "Conceded",
        "last_5": "Last 5 Matches",
        "home": "Home",
        "away": "Away",
        "points": "points",
        "select_team": "Select Team (search)",
        "place_bet": "Place Bet",
        "stake": "Stake (units)",
        "bet_success": "Bet saved successfully!",
        "invalid_stake": "Please enter a valid stake amount.",
        "kelly_recommendation": "Kelly recommended stake:",
    }
}

SPORTS = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one"
}

TEAM_ID_MAPPING = {
    "Arsenal": 57,
    "Barcelona": 81,
    "Bayern Munich": 5,
    "Juventus": 109,
    "Paris Saint-Germain": 524,
    "Manchester City": 65,
    "Real Madrid": 86,
    "Inter": 108,
    "Napoli": 113,
    "Liverpool": 64,
}

HISTORY_FILE = "bet_history.csv"

# ================ IMPROVEMENTS ================= #
def validate_match(match):
    return all(key in match for key in ['home_team', 'away_team', 'bookmakers', 'id'])

def get_hashed_filename(filename):
    return hashlib.sha256(filename.encode()).hexdigest() + '.csv'

def calculate_kelly(prob, odds):
    if odds <= 1:
        return 0.0
    return (prob * (odds - 1) - (1 - prob)) / (odds - 1)

def get_best_odds(match):
    best_home, best_draw, best_away = 0, 0, 0
    for bookmaker in match.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market['key'] == 'h2h':
                for outcome in market['outcomes']:
                    if outcome['name'] == match['home_team']:
                        best_home = max(best_home, outcome['price'])
                    elif outcome['name'] == 'Draw':
                        best_draw = max(best_draw, outcome['price'])
                    elif outcome['name'] == match['away_team']:
                        best_away = max(best_away, outcome['price'])
    return {'home': best_home, 'draw': best_draw, 'away': best_away}

# ================ API FUNCTIONS ================= #
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
        response.raise_for_status()
        return [m for m in response.json() if validate_match(m)]
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return {}
    try:
        with ThreadPoolExecutor() as executor:
            matches_future = executor.submit(
                requests.get,
                f"https://api.football-data.org/v4/teams/{team_id}/matches",
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                params={"status": "FINISHED", "limit": 20}
            )
            h2h_future = executor.submit(
                requests.get,
                f"https://api.football-data.org/v4/teams/{team_id}/matches",
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                params={"status": "FINISHED", "limit": 5, "head2head": "true"}
            )
            
        matches = matches_future.result().json().get("matches", [])
        h2h = h2h_future.result().json().get("matches", [])
        
        return {
            "last_matches": matches[-10:],
            "h2h": h2h,
            "form": matches[-5:]
        }
    except Exception as e:
        st.error(f"Stats Error for {team_name}: {str(e)}")
        return {}

# ================ ANALYTICS ============== #
def get_extended_stats(matches_data, team_name):
    if not matches_data:
        return {}
    
    stats = {
        'goals_scored': [],
        'goals_conceded': [],
        'wins': 0,
        'draws': 0,
        'losses': 0
    }
    
    for match in matches_data.get('last_matches', []):
        is_home = match['homeTeam']['name'] == team_name
        team_goals = match['score']['fullTime']['home' if is_home else 'away']
        opp_goals = match['score']['fullTime']['away' if is_home else 'home']
        
        stats['goals_scored'].append(team_goals)
        stats['goals_conceded'].append(opp_goals)
        
        if team_goals > opp_goals:
            stats['wins'] += 1
        elif team_goals == opp_goals:
            stats['draws'] += 1
        else:
            stats['losses'] += 1
    
    return {
        'avg_scored': np.mean(stats['goals_scored']) if stats['goals_scored'] else 0,
        'avg_conceded': np.mean(stats['goals_conceded']) if stats['goals_conceded'] else 0,
        'form': stats['wins']*3 + stats['draws'],
        'h2h': matches_data.get('h2h', [])
    }

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

# ================ UI COMPONENTS ================== #
def render_match_comparison(home_stats, away_stats, texts):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(f"{texts['avg_goals']} ({texts['home']})", 
                 f"{home_stats['avg_scored']:.1f}",
                 f"{home_stats['avg_conceded']:.1f} {texts['conceded']}")

    with col2:
        st.write("VS")
        st.write(f"{texts['last_5']}:")
        st.write(f"{texts['home']}: {home_stats['form']} {texts['points']}")
        st.write(f"{texts['away']}: {away_stats['form']} {texts['points']}")

    with col3:
        st.metric(f"{texts['avg_goals']} ({texts['away']})", 
                 f"{away_stats['avg_scored']:.1f}",
                 f"{away_stats['avg_conceded']:.1f} {texts['conceded']}")

def render_kelly_calculator(texts):
    with st.expander(texts['kelly_title']):
        bankroll = st.number_input(texts['bankroll'], min_value=10, value=1000)
        confidence = st.slider(texts['confidence'], 1, 100, 50)
        max_stake = st.slider(texts['max_stake'], 1, 100, 20)
        
        return {
            'bankroll': bankroll,
            'confidence': confidence/100,
            'max_stake': max_stake/100
        }

def save_bet(match_id, team, odds, stake):
    filename = get_hashed_filename(HISTORY_FILE)
    bet_data = {
        "timestamp": pd.Timestamp.now(),
        "match_id": match_id,
        "team": team,
        "odds": odds,
        "stake": stake
    }
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = df.append(bet_data, ignore_index=True)
    else:
        df = pd.DataFrame([bet_data])
    df.to_csv(filename, index=False)

# ================ MAIN APP ====================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor PRO", layout="wide")
    
    lang = st.sidebar.selectbox("Language", list(LANGUAGES.keys()))
    texts = LANGUAGES[lang]
    
    with st.sidebar:
        st.header(texts['settings'])
        min_odds = st.slider(texts['min_odds'], 1.0, 10.0, 1.5)
        kelly_settings = render_kelly_calculator(texts)
    
    st.title("⚽ Smart Betting Analyzer PRO")
    
    league = st.selectbox(texts['select_league'], list(SPORTS.keys()))
    matches = get_live_odds(SPORTS[league])
    
    if not matches:
        st.warning(texts['no_matches'])
        return
    
    # ... предходен код ...

    match_strs = [f"{m['home_team']} vs {m['away_team']}" for m in matches]
    selected_match = st.selectbox(texts['select_match'], match_strs)
    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)

    # Взимаме статистики за двата отбора (паралелно)
    with ThreadPoolExecutor() as executor:
        future_home = executor.submit(get_team_stats, match['home_team'])
        future_away = executor.submit(get_team_stats, match['away_team'])
        home_stats = future_home.result()
        away_stats = future_away.result()

    # Изчисляване на разширена статистика
    home_extended = get_extended_stats(home_stats, match['home_team'])
    away_extended = get_extended_stats(away_stats, match['away_team'])

    # Poisson прогноза
    home_prob, draw_prob, away_prob = calculate_poisson_probabilities(
        home_extended.get('avg_scored', 0),
        away_extended.get('avg_scored', 0)
    )

    # Най-добри коефициенти от API
    best_odds = get_best_odds(match)

    # Показваме сравнение на отборите
    st.subheader(f"{match['home_team']} vs {match['away_team']}")
    render_match_comparison(home_extended, away_extended, texts)

    # Показване на вероятности и коефициенти
    st.write(f"### {texts['predictions']}")
    st.write(f"**{match['home_team']} Win:** {home_prob:.2%} | {texts['odds']}: {best_odds['home']}")
    st.write(f"**Draw:** {draw_prob:.2%} | {texts['odds']}: {best_odds['draw']}")
    st.write(f"**{match['away_team']} Win:** {away_prob:.2%} | {texts['odds']}: {best_odds['away']}")

    # Калкулация стойност (value bet)
    value_home = best_odds['home'] * home_prob - 1
    value_draw = best_odds['draw'] * draw_prob - 1
    value_away = best_odds['away'] * away_prob - 1

    st.write(f"### {texts['value']} (Value Bet)")
    st.write(f"{match['home_team']}: {value_home:.3f}")
    st.write(f"Draw: {value_draw:.3f}")
    st.write(f"{match['away_team']}: {value_away:.3f}")

    # Залог по Кели за най-добрата стойност
    bet_options = {
        match['home_team']: (home_prob, best_odds['home'], value_home),
        "Draw": (draw_prob, best_odds['draw'], value_draw),
        match['away_team']: (away_prob, best_odds['away'], value_away),
    }
    best_bet = max(bet_options.items(), key=lambda x: x[1][2])  # избор по стойност
    prob, odds, val = best_bet[1]

    kelly_fraction = calculate_kelly(prob * kelly_settings['confidence'], odds)
    kelly_fraction = min(kelly_fraction, kelly_settings['max_stake'])
    recommended_stake = kelly_fraction * kelly_settings['bankroll']

    st.write(f"### {texts['kelly_recommendation']} {best_bet[0]}")
    st.write(f"{recommended_stake:.2f} единици (Kelly Fraction: {kelly_fraction:.3f})")

    # Възможност за поставяне на залог и записване в историята
    stake = st.number_input(texts['stake'], min_value=0.0, step=1.0, value=0.0)
    if st.button(texts['place_bet']):
        if stake > 0:
            save_bet(match['id'], best_bet[0], odds, stake)
            st.success(texts['bet_success'])
        else:
            st.error(texts['invalid_stake'])

    # История на залозите
    st.sidebar.subheader(texts['bet_history'])
    filename = get_hashed_filename(HISTORY_FILE)
    if os.path.exists(filename):
        history_df = pd.read_csv(filename)
        st.sidebar.dataframe(history_df)
    else:
        st.sidebar.info(texts['no_history'])

if __name__ == "__main__":
    main()
