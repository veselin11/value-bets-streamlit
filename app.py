import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import toml
import time

# Зареждане на API ключа
secrets = toml.load(".streamlit/secrets.toml")
ODDS_API_KEY = secrets["ODDS_API_KEY"]

st.set_page_config(layout="wide")
st.title("📊 Следене на фаворити в реално време")

FAVORITE_THRESHOLD = st.slider("Максимален коефициент за фаворит", 1.1, 2.0, 1.5, 0.05)
ALERT_DIFF = st.slider("Сигнал при покачване на коеф. с поне:", 0.1, 1.0, 0.3, 0.05)
REFRESH_INTERVAL = st.slider("Честота на проверка (сек)", 60, 600, 180, 30)

if "initial_odds" not in st.session_state:
    st.session_state.initial_odds = {}
if "last_update" not in st.session_state:
    st.session_state.last_update = 0

def fetch_favorite_matches():
    all_matches = []

    sports_url = "https://api.the-odds-api.com/v4/sports"
    sports_res = requests.get(sports_url, params={"apiKey": ODDS_API_KEY})
    if sports_res.status_code != 200:
        st.error("Грешка при зареждане на спортовете")
        return pd.DataFrame()

    football_leagues = [s for s in sports_res.json() if "soccer" in s["key"] and s["active"]]

    now_utc = datetime.now(timezone.utc)
    min_time = now_utc - timedelta(hours=1)    # 1 час назад
    max_time = now_utc + timedelta(hours=24)   # 24 часа напред

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
                match_time = datetime.fromisoformat(game["commence_time"].replace("Z", "+00:00"))

                # Филтриране за мачове започнали до 1 час назад и в следващите 24 часа
                if not (min_time <= match_time <= max_time):
                    continue

                home = game["home_team"]
                away = game["away_team"]
                league_title = league["title"]
                bookmaker = game["bookmakers"][0]
                outcomes = next(m["outcomes"] for m in bookmaker["markets"] if m["key"] == "h2h")
                odds_dict = {o["name"]: o["price"] for o in outcomes}

                min_odds = min(odds_dict.values())
                if min_odds < FAVORITE_THRESHOLD:
                    favorite = [team for team, odds in odds_dict.items() if odds == min_odds][0]

                    if match_id not in st.session_state.initial_odds:
                        st.session_state.initial_odds[match_id] = min_odds

                    current_odds = min_odds
                    initial_odds = st.session_state.initial_odds[match_id]
                    odds_change = current_odds - initial_odds

                    all_matches.append({
                        "Мач": f"{home} vs {away}",
                        "Лига": league_title,
                        "Начало": match_time.strftime("%Y-%m-%d %H:%M UTC"),
                        "Фаворит": favorite,
                        "Коеф. начален": round(initial_odds, 2),
                        "Коеф. текущ": round(current_odds, 2),
                        "Промяна": round(odds_change, 2),
                        "Сигнал": "🔔" if odds_change >= ALERT_DIFF else ""
                    })

            except Exception:
                continue

    return pd.DataFrame(all_matches)

refresh_clicked = st.button("🔄 Обнови мачовете")

time_since_last = time.time() - st.session_state.last_update
if refresh_clicked or time_since_last > REFRESH_INTERVAL:
    st.session_state.last_update = time.time()
    df = fetch_favorite_matches()
    st.session_state.df = df
else:
    df = st.session_state.get("df", pd.DataFrame())

if df.empty:
    st.warning("Няма намерени мачове с фаворити при зададения праг и в рамките на 25 часа (включително мачове на живо).")
else:
    df_sorted = df.sort_values("Начало")
    signals_count = df_sorted["Сигнал"].value_counts().get("🔔", 0)
    st.markdown(f"### Общо сигнали: {signals_count}")
    st.dataframe(df_sorted, use_container_width=True)

if time.time() - st.session_state.last_update > REFRESH_INTERVAL:
    st.experimental_rerun()
