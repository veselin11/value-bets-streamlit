import streamlit as st
import requests
from datetime import datetime
import pytz

# === Настройки и API ===
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "uk,us,eu,au"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

# === Streamlit Setup ===
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# === Session State ===
if "history" not in st.session_state:
    st.session_state.history = []

if "bank" not in st.session_state:
    st.session_state.bank = 500.0

if "target_profit" not in st.session_state:
    st.session_state.target_profit = 150.0  # 30% от 500

if "days" not in st.session_state:
    st.session_state.days = 5

# === Функция за изчисление на залог ===
def calculate_bet_amount():
    goal = st.session_state.target_profit
    days = st.session_state.days
    bets_per_day = 3
    total_bets = bets_per_day * days
    return round(goal / total_bets, 2)

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Реални мачове от Европа (днес)")

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
                    value_bets.append({
                        "Мач": f"{match['home_team']} vs {match['away_team']}",
                        "Пазар": name,
                        "Коефициент": info['price'],
                        "Букмейкър": info['bookmaker'],
                        "Value %": round((value - 1) * 100, 2),
                        "Начален час": match_time_local.strftime("%H:%M"),
                        "Time": match_time_local.strftime("%Y-%m-%d %H:%M")
                    })

        if value_bets:
            df = sorted(value_bets, key=lambda x: -x["Value %"])
            for i, bet in enumerate(df):
                with st.expander(f"{bet['Мач']} – {bet['Пазар']} @ {bet['Коефициент']}"):
                    st.write(f"**Коефициент:** {bet['Коефициент']}")
                    st.write(f"**Value %:** {bet['Value %']}%")
                    st.write(f"**Букмейкър:** {bet['Букмейкър']}")
                    st.write(f"**Начален час:** {bet['Начален час']}")
                    if st.button("Залагай", key=f"bet_{i}"):
                        amount = calculate_bet_amount()
                        st.session_state.history.append({
                            "Мач": bet['Мач'],
                            "Пазар": bet['Пазар'],
                            "Коефициент": bet['Коефициент'],
                            "Value %": bet['Value %'],
                            "Час": bet['Time'],
                            "Залог": amount
                        })
                        st.success(f"Заложено: {amount} лв. на {bet['Пазар']} @ {bet['Коефициент']}")

        else:
            st.info("Няма стойностни залози за днешните мачове в момента.")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залози")
    if st.session_state.history:
        st.dataframe(st.session_state.history, use_container_width=True)
    else:
        st.info("Все още няма залози.")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки на банката и целта")
    st.number_input("Начална банка (лв)", min_value=0.0, step=10.0,
                    value=st.session_state.bank, key="bank")
    st.number_input("Целева печалба (лв)", min_value=0.0, step=10.0,
                    value=st.session_state.target_profit, key="target_profit")
    st.number_input("Целева продължителност (дни)", min_value=1, max_value=30,
                    value=st.session_state.days, key="days")

    st.markdown(f"**Предложена сума за единичен залог:** {calculate_bet_amount()} лв.")
