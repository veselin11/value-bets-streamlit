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

TEAM_ID_MAPPING = {
    # English Premier League
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
    "Luton Town": 389,
    "Manchester City": 65,
    "Manchester United": 66,
    "Newcastle United": 67,
    "Nottingham Forest": 351,
    "Sheffield United": 356,
    "Tottenham Hotspur": 73,
    "West Ham United": 563,
    "Wolves": 76,
    "Bournemouth": 1044,
    
    # Australian A-League
    "Melbourne City": 1833,
    "Western United FC": 111974,
    "Sydney FC": 1838,
    "Melbourne Victory": 1837,
    
    # Add more leagues as needed
}

# ================== API FUNCTIONS ================== #
@st.cache_data(ttl=3600)
def get_soccer_sports():
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY}
        )
        response.raise_for_status()
        sports = response.json()
        
        valid_sports = []
        for sport in sports:
            if (sport.get('group') == 'Soccer' and 
                'h2h' in sport.get('markets', [])):
                valid_sports.append(sport['key'])
        
        return valid_sports
    except Exception as e:
        st.error(f"Sports API Error: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_live_odds():
    try:
        all_matches = []
        soccer_sports = get_soccer_sports()
        
        for sport in soccer_sports:
            try:
                response = requests.get(
                    f"https://api.the-odds-api.com/v4/sports/{sport}/odds",
                    params={
                        "apiKey": ODDS_API_KEY,
                        "regions": "eu",
                        "markets": "h2h",
                        "oddsFormat": "decimal"
                    },
                    timeout=15
                )
                
                if response.status_code == 422:
                    continue  # Skip unsupported markets
                
                response.raise_for_status()
                matches = response.json()
                
                for match in matches:
                    match['sport_key'] = sport
                all_matches.extend(matches)
            
            except requests.exceptions.RequestException as e:
                continue
        
        return all_matches
    
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
            params={"status": "FINISHED", "limit": 20}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        return []

# ================== ANALYTICS & UI FUNCTIONS ================== #
# (Keep all the analytics and UI functions the same as previous version)
# ...

# ================== MAIN INTERFACE ================== #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Global Football Betting Analyzer")

    with st.spinner("Loading matches from all leagues..."):
        matches = get_live_odds()

    if not matches:
        st.warning("No matches available")
        return

    # Add league filter
    leagues = list(set(m['sport_key'] for m in matches))
    selected_league = st.selectbox("Filter by League:", leagues)
    
    filtered_matches = [m for m in matches if m['sport_key'] == selected_league]
    
    selected_match = st.selectbox(
        "Select Match:",
        [f'{m["home_team"]} vs {m["away_team"]} ({m["sport_key"]})' 
         for m in filtered_matches],
        index=0
    )
    
    # Rest of the code remains the same...
    # ...

if __name__ == "__main__":
    main()
