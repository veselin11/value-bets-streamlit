import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import toml

# Зареждане на ключа от secrets.toml
secrets = toml.load(".streamlit/secrets.toml")
ODDS_API_KEY = secrets["ODDS_API_KEY"]

st.title("📡 Тест: Зареждане на всички активни футболни мачове от ODDS API")

def fetch_all_football_odds():
    all_matches = []

    # 1. Взимане на всички спортове
    sports_url = "https://api.the-odds-api.com/v4/sports"
    res = requests.get(sports_url, params={"apiKey": ODDS_API_KEY})
    if res.status_code != 200:
        st.error("Грешка при зареждане на спортовете")
        return []

    sports = res.json()

    # 2. Филтриране на активни футболни лиги
    football_leagues = [s for s in sports if "soccer" in s["key"] and s["active"]]

    # 3. Зареждане на коефициенти за всяка лига
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

        odds_data = odds_res.json()

        for game in odds_data:
            try:
                match_time = game["commence_time"].replace("T", " ").replace("Z", "")
                home = game["home_team"]
                away = game["away_team"]
                league_title = league["title"]
                bookmaker = game["bookmakers"][0]
                outcomes = next(m["outcomes"] for m in bookmaker["markets"] if m["key"] == "h2h")
                odds_dict = {o["name"]: o["price"] for o in outcomes}
                all_matches.append({
                    "Лига": league_title,
                    "Мач": f"{home} vs {away}",
                    "Начало": match_time,
                    "Коеф. 1": odds_dict.get(home, ""),
                    "Коеф. 2": odds_dict.get(away, "")
                })
            except Exception:
                continue

    return pd.DataFrame(all_matches)

# Бутон за зареждане
if st.button("🔄 Зареди мачове"):
    df = fetch_all_football_odds()
    if not df.empty:
        df["Начало"] = pd.to_datetime(df["Начало"])
        df = df.sort_values("Начало")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Няма активни мачове в момента.")
