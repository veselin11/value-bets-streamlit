import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime
import matplotlib.pyplot as plt
import os

# ================ CONFIGURATION ================= #
FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

SPORTS = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one",
    "Championship": "soccer_efl_champ",
    "Eredivisie": "soccer_netherlands_eredivisie"
}

HISTORY_FILE = "bet_history.csv"

# ================ API FUNCTIONS ================= #
@st.cache_data(ttl=3600)
def get_live_odds(league_key):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{league_key}/odds",
            params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Odds API Error: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    try:
        # Търсим отбор по име, за да вземем неговия ID от Football Data API
        search_response = requests.get(
            "https://api.football-data.org/v4/teams",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY}
        )
        search_response.raise_for_status()
        teams = search_response.json().get("teams", [])
        team_id = None
        for t in teams:
            if t["name"].lower() == team_name.lower():
                team_id = t["id"]
                break
        if not team_id:
            st.warning(f"Отборът '{team_name}' не е намерен в Football Data API.")
            return []
        # Взимаме последните 20 завършени мача на отбора
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 20}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Грешка при зареждане на статистика за {team_name}: {str(e)}")
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

def get_team_stats_data(matches, team_name, is_home=True):
    if not matches:
        return {"avg_goals": 1.2 if is_home else 0.9, "win_rate": 0.5 if is_home else 0.3}
    goals = []
    wins = 0
    count = 0
    for match in matches:
        # Проверка дали този мач е с участието на отбора, и дали той е домакин или гост
        if match["homeTeam"]["name"].lower() == team_name.lower():
            team_goals = match["score"]["fullTime"]["home"]
            opp_goals = match["score"]["fullTime"]["away"]
            is_team_home = True
        elif match["awayTeam"]["name"].lower() == team_name.lower():
            team_goals = match["score"]["fullTime"]["away"]
            opp_goals = match["score"]["fullTime"]["home"]
            is_team_home = False
        else:
            continue

        goals.append(team_goals)
        if team_goals > opp_goals:
            wins += 1
        count += 1
        if count >= 10:
            break

    if count == 0:
        return {"avg_goals": 1.2 if is_home else 0.9, "win_rate": 0.5 if is_home else 0.3}
    return {"avg_goals": np.mean(goals), "win_rate": wins / count}

def plot_probabilities(title, labels, probabilities):
    fig, ax = plt.subplots()
    ax.bar(labels, probabilities, color=["#4CAF50", "#FFC107", "#2196F3"])
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.set_ylabel("Вероятност")
    st.pyplot(fig)

def format_date(iso_date):
    try:
        return datetime.fromisoformat(iso_date.replace("Z","")).strftime("%d %b %Y")
    except:
        return iso_date

# ================ HISTORY ======================= #
def save_history(match, probabilities, odds, chosen):
    row = {
        "datetime": datetime.now().isoformat(),
        "match": f"{match['home_team']} vs {match['away_team']}",
        "prob_home": probabilities[0],
        "prob_draw": probabilities[1],
        "prob_away": probabilities[2],
        "odds_home": odds["home"],
        "odds_draw": odds["draw"],
        "odds_away": odds["away"],
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
        filter_team = st.text_input("Филтрирай по отбор (частично име):")
        if filter_team:
            df = df[df['match'].str.contains(filter_team, case=False)]
        st.dataframe(df)
    else:
        st.info("Все още няма записана история.")

# ================ MAIN APP ========================= #
def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    selected_league = st.selectbox("Изберете първенство:", list(SPORTS.keys()))
    league_key = SPORTS[selected_league]

    with st.spinner("Зареждане на мачове..."):
        matches = get_live_odds(league_key)

    if not matches:
        st.warning("Няма налични мачове в момента.")
        return

    match_options = [f"{m['home_team']} vs {m['away_team']}" for m in matches]
    selected_match = st.selectbox("Изберете мач:", match_options)

    match = next(m for m in matches if f"{m['home_team']} vs {m['away_team']}" == selected_match)

    with st.spinner("Зареждане на статистика за отборите..."):
        home_matches = get_team_stats(match["home_team"])
        away_matches = get_team_stats(match["away_team"])

        home_stats = get_team_stats_data(home_matches, match["home_team"], is_home=True)
        away_stats = get_team_stats_data(away_matches, match["away_team"], is_home=False)

    # Опитваме се да вземем най-добрите коефициенти от всички букмейкъри
    try:
        best_odds = {
            "home": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["home_team"]),
            "draw": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == "Draw"),
            "away": max(o["price"] for b in match["bookmakers"] for o in b["markets"][0]["outcomes"] if o["name"] == match["away_team"])
        }
    except Exception:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}

    prob = calculate_poisson_probabilities(home_stats["avg_goals"], away_stats["avg_goals"])

    tab1, tab2 = st.tabs(["Анализ на мача", "История на отборите"])

    with tab1:
        cols = st.columns(3)
        outcomes = [
            (match["home_team"], prob[0], best_odds["home"]),
            ("Равен", prob[1], best_odds["draw"]),
            (match["away_team"], prob[2], best_odds["away"])
        ]
        for col, (label, probability, odds) in zip(cols, outcomes):
            col.metric(label, f"{probability*100:.1f}%")
            col.write(f"Коефициент: {odds:.2f}")

        plot_probabilities(f"Вероятности за {match['home_team']} vs {match['away_team']}",
                           [match["home_team"], "Равен", match["away_team"]], prob)

        chosen = st.radio("Изберете залог за запазване:", [match["home_team"], "Равен", match["away_team"]])

        if st.button("Запази залог"):
            save_history(match, prob, best_odds, chosen)
            st.success("Залогът е запазен!")

    with tab2:
        st.subheader(f"Последни 10 мача на {match['home_team']}")
        if home_matches:
            for m in home_matches[:10]:
                date = format_date(m["utcDate"])
                score = m["score"]["fullTime"]
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                result = f"{score['home']} - {score['away']}"
                st.write(f"{date} | {home} vs {away} | {result}")
        else:
            st.write("Няма данни за последните мачове.")

        st.subheader(f"Последни 10 мача на {match['away_team']}")
        if away_matches:
            for m in away_matches[:10]:
                date = format_date(m["utcDate"])
                score = m["score"]["fullTime"]
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                result = f"{score['home']} - {score['away']}"
                st.write(f"{date} | {home} vs {away} | {result}")
        else:
            st.write("Няма данни за последните мачове.")

        st.subheader("Директни срещи между двата отбора")
        # Взимаме директни срещи, които са в последните мачове на домакин (home_matches)
        direct_matches = [m for m in home_matches if
                          (m["homeTeam"]["name"].lower() == match["away_team"].lower() or
                           m["awayTeam"]["name"].lower() == match["away_team"].lower())]

        if direct_matches:
            for m in direct_matches[:10]:
                date = format_date(m["utcDate"])
                score = m["score"]["fullTime"]
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                result = f"{score['home']} - {score['away']}"
                st.write(f"{date} | {home} vs {away} | {result}")
        else:
            st.write("Няма директни срещи между двата отбора в последните мачове.")

    st.markdown("---")
    st.subheader("История на запазените залози")
    display_history()

if __name__ == "__main__":
    main()
