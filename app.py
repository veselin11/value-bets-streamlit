import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import toml
import time

# Зареждане на API ключа
secrets = toml.load(".streamlit/secrets.toml")
ODDS_API_KEY = secrets["ODDS_API_KEY"]

st.set_page_config(layout="wide")
st.title("📊 Следене на фаворити в реално време")

FAVORITE_THRESHOLD = st.slider("Максимален коефициент за фаворит", min_value=1.1, max_value=2.0, value=1.5, step=0.05)
ALERT_DIFF = st.slider("Сигнал при покачване на коеф. с поне:", min_value=0.1, max_value=1.0, value=0.3, step=0.05)
REFRESH_INTERVAL = st.slider("Честота на проверка (сек)", min_value=60, max_value=600, value=180, step=30)

# Състояние: стартови коефициенти
if "initial_odds" not in st.session_state:
    st.session_state.initial_odds = {}

def fetch_favorite_matches():
    all_matches = []

    sports_url = "https://api.the-odds-api.com/v4/sports"
    sports_res = requests.get(sports_url, params={"apiKey": ODDS_API_KEY})
    if sports_res.status_code != 200:
        st.error("Грешка при зареждане на спортовете")
        return []

    football_leagues = [s for s in sports_res.json() if "soccer" in s["key"] and s["active"]]

    for league in football_leagues:
        odds_url = f"https://api.the-odds-api.com/v4/sports/{league['key']}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        odds_res = requests.get(odds_url, params=params)
        if odds_res.status_code != 200:
            continue

        for game in odds_res.json():
            try:
                match_id = game["id"]
                match_time = game["commence_time"].replace("T", " ").replace("Z", "")
                home = game["home_team"]
                away = game["away_team"]
                league_title = league["title"]
                bookmaker = game["bookmakers"][0]
                outcomes = next(m["outcomes"] for m in bookmaker["markets"] if m["key"] == "h2h")
                odds_dict = {o["name"]: o["price"] for o in outcomes}

                min_odds = min(odds_dict.values())
                if min_odds < FAVORITE_THRESHOLD:
                    favorite = [team for team, odds in odds_dict.items() if odds == min_odds][0]

                    # Запазваме първоначалния коефициент
                    if match_id not in st.session_state.initial_odds:
                        st.session_state.initial_odds[match_id] = min_odds

                    current_odds = min_odds
                    initial_odds = st.session_state.initial_odds[match_id]
                    odds_change = current_odds - initial_odds

                    all_matches.append({
                        "Мач": f"{home} vs {away}",
                        "Лига": league_title,
                        "Начало": match_time,
                        "Фаворит": favorite,
                        "Коеф. начален": round(initial_odds, 2),
                        "Коеф. текущ": round(current_odds, 2),
                        "Промяна": round(odds_change, 2),
                        "Сигнал": "🔔" if odds_change >= ALERT_DIFF else ""
                    })

            except Exception:
                continue

    return pd.DataFrame(all_matches)

if st.button("🔄 Обнови мачовете"):
    with st.spinner("Зареждане..."):
        df = fetch_favorite_matches()
        if not df.empty:
            df["Начало"] = pd.to_datetime(df["Начало"])
            df = df.sort_values("Начало")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Няма намерени мачове с фаворити при зададения праг.")
            
