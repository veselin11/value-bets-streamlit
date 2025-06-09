import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import time

API_KEY = st.secrets["ODDS_API_KEY"]

LEAGUES = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Bundesliga": "soccer_germany_bundesliga",
}

@st.cache_data(ttl=300)
def fetch_odds(league_code):
    url = f"https://api.the-odds-api.com/v4/sports/{league_code}/odds"
    r = requests.get(url, params={
        "apiKey": API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"
    })
    return r.json() if r.status_code == 200 else []

def filter_favorites_today(games, threshold=1.5):
    out = []
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    for g in games:
        ct = datetime.fromisoformat(g["commence_time"].replace("Z","+00:00"))
        if not (today_start <= ct <= today_end):
            continue
        try:
            h2h = next(m for m in g["bookmakers"][0]["markets"] if m["key"]=="h2h")
            fav = min(h2h["outcomes"], key=lambda x: x["price"])
            if fav["price"] <= threshold:
                out.append({
                    "game_id": g["id"], "commence": ct, "home": g["home_team"],
                    "away": g["away_team"], "fav_name": fav["name"],
                    "initial": fav["price"], "sport": g["sport_title"]
                })
        except:
            continue
    return sorted(out, key=lambda x: x["commence"])

st.title("🎯 Днешни фаворити със сигнали")
selected_league = st.sidebar.selectbox("Лига", list(LEAGUES.keys()))
league_code = LEAGUES[selected_league]
increase_thr = st.sidebar.slider("Праг (всяко покачване от)", 0.05, 1.0, 0.2, 0.05)
refresh = st.sidebar.slider("Авто обновяване (сек)", 30, 600, 300, 30)
sound = st.sidebar.checkbox("Звуков сигнал", False)

games = fetch_odds(league_code)
st.markdown("**Всички мачове от API:**")
st.write(pd.DataFrame([{"home":g["home_team"], "away":g["away_team"], "time":g["commence_time"]} for g in games]))

favs = filter_favorites_today(games)
if not favs:
    st.info("Няма днешни фаворити с начален коефициент ≤1.5")
else:
    if "prev" not in st.session_state: st.session_state.prev = {}
    alerts = []
    data = []
    for f in favs:
        current = next((o["price"] for g in games if g["id"]==f["game_id"]
                        for bk in g["bookmakers"][:1]
                        for m in bk["markets"] if m["key"]=="h2h"
                        for o in m["outcomes"] if o["name"]==f["fav_name"]
                       ), None)
        prev = st.session_state.prev.get(f["game_id"], f["initial"])
        if current and (current - prev) >= increase_thr:
            alerts.append(f"⚠️ {f['home']} vs {f['away']}: {f['fav_name']} от {prev:.2f} → {current:.2f}")
            if sound:
                st.audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg")
        st.session_state.prev[f["game_id"]] = current
        data.append({
            "Лига": f["sport"], "Мач": f"{f['home']} vs {f['away']}",
            "Начален": f["initial"], "Текущ": current
        })
    st.dataframe(pd.DataFrame(data))
    for a in alerts: st.warning(a)

st.write(f"↻ Обновяване след {refresh} сек.")
time.sleep(refresh)
st.experimental_rerun()
