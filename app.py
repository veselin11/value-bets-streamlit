import streamlit as st
import requests
from datetime import datetime
import pytz
import math

# === Настройки ===
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "uk,us,eu,au"
MARKETS = "h2h,totals,spreads"  # Добавени пазари
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

# === Начални стойности ===
if "bank" not in st.session_state:
    st.session_state.bank = 500.0
if "goal_profit" not in st.session_state:
    st.session_state.goal_profit = 150.0  # 30% от 500
if "days_to_achieve" not in st.session_state:
    st.session_state.days_to_achieve = 5
if "history" not in st.session_state:
    st.session_state.history = []

# === Интерфейс ===
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Реални мачове от Европа (днес)")
    st.caption("Данни от OddsAPI в реално време")

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
                    if market['key'] not in ['h2h', 'totals', 'spreads']:
                        continue
                    for outcome in market['outcomes']:
                        label = f"{market['key'].upper()} – {outcome['name']}"
                        price = outcome['price']
                        if label not in best_odds or price > best_odds[label]['price']:
                            best_odds[label] = {
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
                        "match_id": match['id'],
                        "outcome": name
                    })

        if value_bets:
            sorted_bets = sorted(value_bets, key=lambda x: -x["Value %"])
            selected = st.selectbox("Избери залог:", [f"{b['Мач']} | {b['Пазар']} | @ {b['Коефициент']}" for b in sorted_bets])
            selected_bet = next(b for b in sorted_bets if f"{b['Мач']} | {b['Пазар']} | @ {b['Коефициент']}" in selected)

            # Логика за сума на залог
            remaining_profit = st.session_state.goal_profit
            bet_days = st.session_state.days_to_achieve
            target_profit_per_day = remaining_profit / bet_days
            implied_prob = 1 / selected_bet["Коефициент"]
            stake = target_profit_per_day / (selected_bet["Коефициент"] - 1)
            stake = min(st.session_state.bank, stake)
            stake = math.ceil(stake / 10) * 10  # Кръгло до 10

            st.markdown(f"**Предложен залог:** {selected_bet['Мач']} – {selected_bet['Пазар']} @ {selected_bet['Коефициент']}")
            st.markdown(f"**Сума за залог:** {stake:.2f} лв")
            if st.button("Заложи"):
                st.session_state.history.append({
                    "Дата": datetime.now(local_tz).strftime("%Y-%m-%d %H:%M"),
                    "Мач": selected_bet["Мач"],
                    "Пазар": selected_bet["Пазар"],
                    "Коефициент": selected_bet["Коефициент"],
                    "Залог": stake,
                    "Статус": "Изчаква"
                })
                st.session_state.bank -= stake
                st.success("Залогът е добавен към историята.")
        else:
            st.info("Няма стойностни залози за днес в момента.")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залози")
    if len(st.session_state.history) == 0:
        st.info("Няма направени залози.")
    else:
        st.dataframe(st.session_state.history, use_container_width=True)

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки")
    st.number_input("Начална банка (лв)", min_value=10.0, value=st.session_state.bank, step=10.0, key="bank")
    st.number_input("Целева печалба (лв)", min_value=10.0, value=st.session_state.goal_profit, step=10.0, key="goal_profit")
    st.number_input("Брой дни до целта", min_value=1, value=st.session_state.days_to_achieve, step=1, key="days_to_achieve")
