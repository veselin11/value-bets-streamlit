import streamlit as st
import requests
import numpy as np
from scipy.stats import poisson
import joblib

FOOTBALL_DATA_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
ODDS_API_KEY = st.secrets["ODDS_API_KEY"]

TEAM_ID_MAPPING = {
    "Manchester City": 65,
    "AFC Bournemouth": 1044,
    "Liverpool": 64,
    "Everton": 62,
    "Arsenal": 57,
    "Tottenham Hotspur": 73,
    # ... добави още отбори ако искаш
}

@st.cache_data(ttl=3600)
def get_sports():
    try:
        response = requests.get("https://api.the-odds-api.com/v4/sports", params={"apiKey": ODDS_API_KEY})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Грешка при взимане на първенства: {e}")
        return []

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
        return response.json()
    except Exception as e:
        st.error(f"Грешка при взимане на коефициенти: {e}")
        return []

@st.cache_data(ttl=3600)
def get_team_stats(team_name):
    team_id = TEAM_ID_MAPPING.get(team_name)
    if not team_id:
        return None
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
            params={"status": "FINISHED", "limit": 20}
        )
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        st.error(f"Грешка при взимане на статистики за {team_name}: {e}")
        return None

def calculate_poisson_probabilities(home_avg, away_avg):
    home_win, draw, away_win = 0, 0, 0
    for i in range(6):
        for j in range(6):
            p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p
    return home_win, draw, away_win

def calculate_value_bets(probabilities, odds):
    value = {}
    for outcome in ['home', 'draw', 'away']:
        if odds[outcome] == 0:
            value[outcome] = 0
        else:
            implied_prob = 1 / odds[outcome]
            value[outcome] = probabilities[outcome] - implied_prob
    return value

def predict_with_ai(home_stats, away_stats):
    try:
        model = joblib.load("model.pkl")
        scaler = joblib.load("scaler.pkl")
        features = np.array([
            home_stats["avg_goals"],
            away_stats["avg_goals"],
            home_stats["win_rate"],
            away_stats["win_rate"]
        ]).reshape(1, -1)
        scaled_features = scaler.transform(features)
        prediction = model.predict_proba(scaled_features)
        return prediction[0]
    except Exception as e:
        st.error(f"Грешка при AI прогноза: {e}")
        return None

def get_best_odds(match):
    best_odds = {"home": 0, "draw": 0, "away": 0}
    for bookmaker in match.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") == "h2h":
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price", 0)
                    if name == match["home_team"] and price > best_odds["home"]:
                        best_odds["home"] = price
                    elif name == "Draw" and price > best_odds["draw"]:
                        best_odds["draw"] = price
                    elif name == match["away_team"] and price > best_odds["away"]:
                        best_odds["away"] = price
    return best_odds

def process_team_stats(matches, is_home):
    if not matches:
        return {"avg_goals": 1.0, "win_rate": 0.5}
    goals = []
    wins = 0
    for m in matches[-10:]:
        score = m["score"]["fullTime"]
        if is_home:
            goals.append(score["home"])
            if score["home"] > score["away"]:
                wins += 1
        else:
            goals.append(score["away"])
            if score["away"] > score["home"]:
                wins += 1
    if len(matches) >= 10:
        win_rate = wins / 10
    elif len(matches) > 0:
        win_rate = wins / len(matches)
    else:
        win_rate = 0
    avg_goals = np.mean(goals) if goals else 1.0
    return {"avg_goals": avg_goals, "win_rate": win_rate}

def main():
    st.set_page_config(page_title="Advanced Bet Analyzer", layout="wide", page_icon="⚽")
    st.title("🔮 Advanced Bet Analyzer")

    # Избор на първенство
    sports = get_sports()
    if not sports:
        st.warning("Не може да се заредят първенствата")
        return
    sport_options = {sport["title"]: sport["key"] for sport in sports}
    selected_sport_title = st.selectbox("Избери първенство", list(sport_options.keys()))
    selected_sport_key = sport_options[selected_sport_title]

    # Вземане на мачове с коефициенти
    matches = get_live_odds(selected_sport_key)
    if not matches:
        st.warning("Няма налични мачове за това първенство в момента")
        return

    selected_match_str = st.selectbox(
        "Избери мач за анализ:",
        [f'{m["home_team"]} vs {m["away_team"]}' for m in matches]
    )
    match = next(m for m in matches if f'{m["home_team"]} vs {m["away_team"]}' == selected_match_str)

    # Взимане статистики за отборите
    home_stats_raw = get_team_stats(match["home_team"])
    away_stats_raw = get_team_stats(match["away_team"])

    home_stats = process_team_stats(home_stats_raw, True)
    away_stats = process_team_stats(away_stats_raw, False)

    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"], away_stats["avg_goals"]
    )

    best_odds = get_best_odds(match)

    value_bets = calculate_value_bets(
        {"home": prob_home, "draw": prob_draw, "away": prob_away},
        best_odds
    )

    tab1, tab2, tab3 = st.tabs(["Основен анализ", "Разширена статистика", "AI Прогнози"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader(f"🏠 {match['home_team']}")
            st.metric("Средни голове", f"{home_stats['avg_goals']:.2f}")
            st.metric("Шанс за победа", f"{prob_home*100:.1f}%")
            st.metric("Value Score", f"{value_bets['home']*100:.1f}%", delta="Стойностен" if value_bets['home'] > 0 else "Нестойностен")

        with col2:
            st.subheader("⚖ Равен")
            st.metric("Шанс", f"{prob_draw*100:.1f}%")
            st.metric("Value Score", f"{value_bets['draw']*100:.1f}%", delta="Стойностен" if value_bets['draw'] > 0 else "Нестойностен")

        with col3:
            st.subheader(f"✈ {match['away_team']}")
            st.metric("Средни голове", f"{away_stats['avg_goals']:.2f}")
            st.metric("Шанс за победа", f"{prob_away*100:.1f}%")
            st.metric("Value Score", f"{value_bets['away']*100:.1f}%", delta="Стойностен" if value_bets['away'] > 0 else "Нестойностен")

    with tab2:
        st.subheader("📈 Исторически показатели")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Последни 5 мача {match['home_team']}:**")
            if home_stats_raw:
                for m in home_stats_raw[-5:]:
                    result = f"{m['score']['fullTime']['home']}-{m['score']['fullTime']['away']}"
                    st.write(f"- {result} ({m['utcDate'][:10]})")
        with col2:
            st.write(f"**Последни 5 мача {match['away_team']}:**")
            if away_stats_raw:
                for m in away_stats_raw[-5:]:
                    result = f"{m['score']['fullTime']['away']}-{m['score']['fullTime']['home']}"
                    st.write(f"- {result} ({m['utcDate'][:10]})")

    with tab3:
        st.subheader("🤖 AI Прогноза")
        if st.button("Генерирай прогноза"):
            ai_prediction = predict_with_ai(home_stats, away_stats)
            if ai_prediction is not None:
                st.write("### Вероятности:")
                st.write(f"- Победа {match['home_team']}: {ai_prediction[0]*100:.1f}%")
                st.write(f"- Равен: {ai_prediction[1]*100:.1f}%")
                st.write(f"- Победа {match['away_team']}: {ai_prediction[2]*100:.1f}%")

if __name__ == "__main__":
    main()
