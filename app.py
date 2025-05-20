import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from utils import calculate_implied_probability, calculate_value_bets, get_team_stats

# Настройки
API_KEY = "ВЪВЕДИ_ТВОЯ_КЛЮЧ_ЗА_ODDS_API"
SPORT = "soccer_epl"
REGIONS = "eu"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"
BOOKMAKER_PRIORITY = ["pinnacle", "bet365"]

# Зареждане на коефициенти от The Odds API
def load_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error(f"Грешка при взимане на коефициенти: {response.status_code} {response.text}")
        return []
    return response.json()

# Основна логика
@st.cache_data(show_spinner=False)
def process_odds(odds_json):
    matches = []
    for match in odds_json:
        match_time = datetime.fromisoformat(match['commence_time'].replace("Z", "+00:00"))
        if 'bookmakers' not in match:
            continue

        pinnacle = next((b for b in match['bookmakers'] if b['key'] == 'pinnacle'), None)
        if not pinnacle:
            continue

        for bookmaker in match['bookmakers']:
            if bookmaker['key'] not in BOOKMAKER_PRIORITY:
                continue

            for market in bookmaker['markets']:
                if market['key'] != 'h2h':
                    continue

                outcomes = market['outcomes']
                if len(outcomes) < 2:
                    continue

                home_team = match['home_team']
                away_team = match['away_team']
                home_odds = next((o['price'] for o in outcomes if o['name'] == home_team), None)
                away_odds = next((o['price'] for o in outcomes if o['name'] == away_team), None)

                if home_odds and away_odds:
                    # Имплицитна вероятност от Pinnacle
                    pinnacle_market = next((m for m in pinnacle['markets'] if m['key'] == 'h2h'), None)
                    if not pinnacle_market:
                        continue
                    pin_home = next((o['price'] for o in pinnacle_market['outcomes'] if o['name'] == home_team), None)
                    pin_away = next((o['price'] for o in pinnacle_market['outcomes'] if o['name'] == away_team), None)

                    if not pin_home or not pin_away:
                        continue

                    prob_home = calculate_implied_probability(pin_home)
                    prob_away = calculate_implied_probability(pin_away)

                    # Проверка за стойностен залог
                    value_home = calculate_value_bets(prob_home, home_odds)
                    value_away = calculate_value_bets(prob_away, away_odds)

                    if value_home or value_away:
                        stats_home, stats_away = get_team_stats(home_team, away_team)

                        matches.append({
                            "Време": match_time.strftime("%Y-%m-%d %H:%M"),
                            "Мач": f"{home_team} - {away_team}",
                            "Коеф. ДОМАКИН": home_odds,
                            "Коеф. ГОСТ": away_odds,
                            "Вероятн. ДОМАКИН": round(prob_home, 2),
                            "Вероятн. ГОСТ": round(prob_away, 2),
                            "Стойност ДОМАКИН": value_home,
                            "Стойност ГОСТ": value_away,
                            "Форма ДОМАКИН": stats_home,
                            "Форма ГОСТ": stats_away
                        })
    return pd.DataFrame(matches)

# Основен поток на приложението
def main():
    st.title("Стойностни Залози – Английска Висша Лига")
    st.markdown("Търси се стойност в коефициентите чрез сравнение с референтни (Pinnacle)")

    odds_json = load_odds()
    if not odds_json:
        return

    with st.spinner("Анализ на мачове..."):
        df = process_odds(odds_json)

    if df.empty:
        st.warning("Няма открити стойностни залози в момента.")
    else:
        st.success(f"Намерени стойностни залози: {len(df)}")
        st.dataframe(df)

if __name__ == "__main__":
    main()
    
