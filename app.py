import streamlit as st
import requests
from datetime import datetime
import pytz

# API настройки
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "uk,us,eu,au"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Реални мачове от Европа (днес)")
    st.caption("Данни от OddsAPI в реално време")

    # Достъп до стойности от сесията
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

            best_odds = {}
            for bookmaker in match['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            name = outcome['name']
                            price = outcome['price']
                            if name not in best_odds or price > best_odds[name]['price']:
                                best_odds[name] = {
                                    'price': price,
                                    'bookmaker': bookmaker['title']
                                }

            if len(best_odds) < 2:
                continue

            inv_probs = [1 / info['price'] for info in best_odds.values()]
            fair_prob_sum = sum(inv_probs)

            for name, info in best_odds.items():
                fair_prob = (1 / info['price']) / fair_prob_sum
                value = info['price'] * fair_prob
                if value > 1.05:
                    odds = info['price']
                    value_pct = (value - 1)
                    expected_edge = odds * value_pct - 1

                    if expected_edge > 0:
                        stake = daily_goal / expected_edge
                        max_stake = 0.05 * initial_bank  # max 5% от банката
                        stake_final = round(min(stake, max_stake), 2)
                    else:
                        stake_final = "-"

                    value_bets.append({
                        "Мач": f"{match['home_team']} vs {match['away_team']}",
                        "Пазар": name,
                        "Коефициент": odds,
                        "Букмейкър": info['bookmaker'],
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
    st.write("Тук ще се показват и записват направени залози (предстои разработка).")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки")
    st.subheader("Целева печалба и управление на банката")

    initial_bank = st.number_input("Начална банка (лв)", min_value=10.0, value=500.0, step=10.0, key="initial_bank")
    target_profit = st.number_input("Целева печалба за периода (лв)", min_value=10.0, value=150.0, step=10.0, key="target_profit")
    target_days = st.number_input("Продължителност (дни)", min_value=1, value=5, step=1, key="target_days")

    daily_profit_goal = target_profit / target_days
    st.info(f"Необходима дневна печалба: {daily_profit_goal:.2f} лв")
