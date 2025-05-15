import streamlit as st
import requests
from datetime import datetime
import pytz
import math

# API настройки
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "uk,us,eu,au"
MARKETS = "h2h,totals"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Реални мачове от Европа (днес)")
    st.caption("Пазари: Краен изход, Над/Под голове")

    initial_bank = st.session_state.get("initial_bank", 500.0)
    target_profit = st.session_state.get("target_profit", 150.0)
    target_days = st.session_state.get("target_days", 5)
    daily_goal = target_profit / target_days

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.error(f"Грешка при зареждане на данни: {response.status_code} - {response.text}")
    else:
        data = response.json()
        value_bets = []

        for match in data:
            try:
                match_time = datetime.strptime(match['commence_time'], DATE_FORMAT)
                match_time_local = match_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
                if match_time_local.date() != datetime.now(local_tz).date():
                    continue
            except:
                continue

            if 'bookmakers' not in match or len(match['bookmakers']) == 0:
                continue

            for bookmaker in match['bookmakers']:
                for market in bookmaker['markets']:
                    # 1. Пазар: Краен изход (1X2)
                    if market['key'] == 'h2h':
                        outcomes = market['outcomes']
                        if len(outcomes) < 2:
                            continue

                        inv_probs = [1 / o['price'] for o in outcomes]
                        fair_prob_sum = sum(inv_probs)

                        for outcome in outcomes:
                            fair_prob = (1 / outcome['price']) / fair_prob_sum
                            value = outcome['price'] * fair_prob
                            if value > 1.05:
                                odds = outcome['price']
                                value_pct = (value - 1)
                                expected_edge = odds * value_pct - 1

                                stake = daily_goal / expected_edge if expected_edge > 0 else 0
                                stake = min(stake, 0.05 * initial_bank)
                                stake_final = round(math.ceil(stake / 10) * 10)

                                value_bets.append({
                                    "Мач": f"{match['home_team']} vs {match['away_team']}",
                                    "Пазар": outcome['name'],
                                    "Тип": "1X2",
                                    "Коефициент": odds,
                                    "Букмейкър": bookmaker['title'],
                                    "Value %": round(value_pct * 100, 2),
                                    "Начален час": match_time_local.strftime("%H:%M"),
                                    "Залог (лв)": stake_final
                                })

                    # 2. Пазар: Над/Под
                    if market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            if 'point' not in outcome:
                                continue
                            label = f"{'Over' if 'Over' in outcome['name'] else 'Under'} {outcome['point']}"
                            odds = outcome['price']
                            fair_prob = 1 / odds
                            value = odds * fair_prob
                            if value > 1.05:
                                value_pct = (value - 1)
                                expected_edge = odds * value_pct - 1

                                stake = daily_goal / expected_edge if expected_edge > 0 else 0
                                stake = min(stake, 0.05 * initial_bank)
                                stake_final = round(math.ceil(stake / 10) * 10)

                                value_bets.append({
                                    "Мач": f"{match['home_team']} vs {match['away_team']}",
                                    "Пазар": label,
                                    "Тип": "Над/Под",
                                    "Коефициент": odds,
                                    "Букмейкър": bookmaker['title'],
                                    "Value %": round(value_pct * 100, 2),
                                    "Начален час": match_time_local.strftime("%H:%M"),
                                    "Залог (лв)": stake_final
                                })

        if value_bets:
            sorted_bets = sorted(value_bets, key=lambda x: -x["Value %"])
            st.dataframe(sorted_bets, use_container_width=True)
        else:
            st.info("Няма стойностни залози за днешните мачове в момента.")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залози")
    st.write("Тук ще се записват направените залози (предстои).")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки")
    st.subheader("Целева печалба и управление на банката")

    initial_bank = st.number_input("Начална банка (лв)", min_value=10.0, value=500.0, step=10.0, key="initial_bank")
    target_profit = st.number_input("Целева печалба за периода (лв)", min_value=10.0, value=150.0, step=10.0, key="target_profit")
    target_days = st.number_input("Продължителност (дни)", min_value=1, value=5, step=1, key="target_days")

    daily_profit_goal = target_profit / target_days
    st.info(f"Необходима дневна печалба: {daily_profit_goal:.2f} лв")
