import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# --- API настройки ---
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "uk,us,eu,au"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

# --- Настройки ---
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# --- Сесия за история ---
if "history" not in st.session_state:
    st.session_state.history = []

if "bank" not in st.session_state:
    st.session_state.bank = 500.0  # Начална банка по подразбиране

if "target_profit" not in st.session_state:
    st.session_state.target_profit = 150.0  # Цел: 30% печалба

if "period_days" not in st.session_state:
    st.session_state.period_days = 5

# --- ТАБ 1: Прогнози ---
with tabs[0]:
    st.title("Стойностни залози – Реални мачове от Европа (днес)")
    st.caption("Данни от OddsAPI в реално време")

    # Зареждане на коефициенти
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.error(f"Грешка при зареждане: {response.status_code} - {response.text}")
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
                    value_bets.append({
                        "Мач": f"{match['home_team']} vs {match['away_team']}",
                        "Пазар": name,
                        "Коефициент": info['price'],
                        "Value %": round((value - 1) * 100, 2),
                        "Букмейкър": info['bookmaker'],
                        "Начален час": match_time_local.strftime("%H:%M")
                    })

        if value_bets:
            df = sorted(value_bets, key=lambda x: -x["Value %"])
            selected = st.selectbox("Избери залог", options=[f"{x['Мач']} – {x['Пазар']} ({x['Коефициент']})" for x in df])
            selected_row = df[[f"{x['Мач']} – {x['Пазар']} ({x['Коефициент']})" for x in df].index(selected)]

            st.markdown("**Детайли за залог:**")
            st.write(df[selected_row])

            # Изчисление на залог според целта
            profit_per_day = st.session_state.target_profit / st.session_state.period_days
            odds = df[selected_row]["Коефициент"]
            stake = round(profit_per_day / (odds - 1), 2)

            st.success(f"Предложен залог: {stake} лв. за печалба от {round(profit_per_day, 2)} лв.")

            if st.button("Заложи"):
                st.session_state.history.append({
                    "Дата": datetime.now(local_tz).strftime("%d.%m.%Y %H:%M"),
                    "Мач": df[selected_row]["Мач"],
                    "Пазар": df[selected_row]["Пазар"],
                    "Коефициент": odds,
                    "Залог": stake,
                    "Очаквана печалба": round(stake * (odds - 1), 2)
                })
                st.success("Залогът е добавен в историята.")
        else:
            st.info("Няма стойностни залози за днес.")

# --- ТАБ 2: История ---
with tabs[1]:
    st.header("История на залозите")
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        st.dataframe(hist_df, use_container_width=True)
        total_bets = len(hist_df)
        total_staked = sum([x["Залог"] for x in st.session_state.history])
        expected_profit = sum([x["Очаквана печалба"] for x in st.session_state.history])
        roi = (expected_profit / total_staked) * 100 if total_staked > 0 else 0
        st.markdown(f"""
        **Общо залози:** {total_bets}  
        **Общо заложено:** {total_staked:.2f} лв.  
        **Очаквана печалба:** {expected_profit:.2f} лв.  
        **Очакван ROI:** {roi:.2f} %
        """)
    else:
        st.info("Все още няма запазени залози.")

# --- ТАБ 3: Настройки ---
with tabs[2]:
    st.header("Настройки")
    st.session_state.bank = st.number_input("Начална банка (лв)", value=st.session_state.bank)
    st.session_state.target_profit = st.number_input("Целева печалба (лв)", value=st.session_state.target_profit)
    st.session_state.period_days = st.slider("Период за постигане на целта (дни)", 1, 30, st.session_state.period_days)
