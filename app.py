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

def update_bet_status(bet_id, new_status):
    c.execute("UPDATE bets SET status = ? WHERE id = ?", (new_status, bet_id))
    conn.commit()

def delete_bet(bet_id):
    c.execute("DELETE FROM bets WHERE id = ?", (bet_id,))
    conn.commit()

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
        st.error(f"Failed to fetch data: {res.status_code}")
        return None

# ------------------- Streamlit App -------------------
st.title("📊 Betting Tracker")

# ---------- Manual Bet Entry ----------
with st.expander("➕ Add Bet Manually", expanded=True):
    with st.form("manual_bet_form"):
        date = st.date_input("Date", value=datetime.today())
        match = st.text_input("Match")
        market = st.selectbox("Market", ["Home Win", "Draw", "Away Win"])
        odds = st.number_input("Odds", min_value=1.0, step=0.1, format="%.2f")
        stake = st.number_input("Stake ($)", min_value=0.0, step=10.0, format="%.2f")
        is_value_bet = st.checkbox("Value Bet?")
        status = st.selectbox("Status", ["open", "won", "lost"])
        
        if st.form_submit_button("Add Bet"):
            add_bet(
                date=str(date),
                match=match,
                market=market,
                odds=odds,
                stake=stake,
                status=status,
                is_value_bet=int(is_value_bet)
            )
            st.success("Bet added successfully!")

# ---------- Bet Management ----------
st.subheader("📋 Current Bets")
bets_df = get_bets()

if not bets_df.empty:
    bets_df = bets_df.sort_values(by="date", ascending=False)
    
    # Convert to more readable format
    bets_df['date'] = pd.to_datetime(bets_df['date']).dt.date
    bets_df['is_value_bet'] = bets_df['is_value_bet'].astype(bool)
    
    # Status update and deletion
    for _, row in bets_df.iterrows():
        cols = st.columns([3, 2, 2, 1, 1])
        cols[0].write(f"**{row['match']}**")
        cols[1].write(f"{row['market']} @ {row['odds']}")
        cols[2].write(f"${row['stake']}")
        
        # Status update
        new_status = cols[3].selectbox(
            "Status",
            ["open", "won", "lost"],
            index=["open", "won", "lost"].index(row['status']),
            key=f"status_{row['id']}"
        )
        
        if new_status != row['status']:
            update_bet_status(row['id'], new_status)
            st.experimental_rerun()
        
        # Delete button
        if cols[4].button("❌", key=f"delete_{row['id']}"):
            delete_bet(row['id'])
            st.experimental_rerun()
            
        st.divider()
else:
    st.info("No bets recorded yet")

# ---------- Odds API Section ----------
st.subheader("🔍 Find Odds")
selected_league = st.selectbox("Select League", list(LEAGUES.keys()))
league_key = LEAGUES[selected_league]

if st.button("Fetch Latest Odds"):
    odds_data = get_odds_data(league_key)
    
    if odds_data:
        for match in odds_data:
            commence_time = datetime.strptime(match['commence_time'], "%Y-%m-%dT%H:%M:%SZ")
            commence_date = commence_time.date()
            
            with st.expander(f"**{match['home_team']} vs {match['away_team']}** - {commence_date}"):
                bookmaker_data = []
                
                for bookmaker in match['bookmakers']:
                    for market in bookmaker['markets']:
                        if market['key'] == 'h2h':
                            outcomes = {o['name']: o['price'] for o in market['outcomes']}
                            bookmaker_data.append({
                                'bookmaker': bookmaker['title'],
                                'home': outcomes.get(match['home_team'], 'N/A'),
                                'draw': outcomes.get('Draw', 'N/A'),
                                'away': outcomes.get(match['away_team'], 'N/A')
                            })
                
                if bookmaker_data:
                    df = pd.DataFrame(bookmaker_data)
                    st.dataframe(df.style.highlight_min(axis=0, color='#FFCCCB'), 
                                hide_index=True, 
                                use_container_width=True)
                else:
                    st.warning("No odds available for this match")

# Close connection on app exit
conn.close()
