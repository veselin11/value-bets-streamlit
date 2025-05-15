import streamlit as st import requests from datetime import datetime import pytz import math

Настройки

API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8" SPORT = "soccer" REGIONS = "eu" ODDS_FORMAT = "decimal" DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ" local_tz = pytz.timezone("Europe/Sofia")

Настройки за цел и банка

TARGET_PROFIT = st.sidebar.number_input("Целева печалба (лв)", value=150.0) DAYS = st.sidebar.number_input("Брой дни", value=5) START_BANKROLL = st.sidebar.number_input("Начална банка (лв)", value=500.0)

daily_target = TARGET_PROFIT / DAYS

def calculate_bet_amount(odds): if odds <= 1.01: return 0 raw_amount = daily_target / (odds - 1) return int(math.ceil(raw_amount / 10.0) * 10)  # Кръгло на 10

st.set_page_config(page_title="Стойностни залози", layout="wide") tabs = st.tabs(["Прогнози", "История", "Настройки"])

=== ТАБ 1: Прогнози ===

with tabs[0]: st.title("Стойностни залози – Реални мачове от Европа (днес)") st.caption("Данни от OddsAPI в реално време")

url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
desired_markets = ["h2h", "totals", "spreads"]
supported_markets = []
all_value_bets = []

for market in desired_markets:
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": market,
        "oddsFormat": ODDS_FORMAT
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        st.warning(f"Пазарът '{market}' не е наличен или не се поддържа. Пропуснат.")
        continue

    supported_markets.append(market)
    data = response.json()

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
            for mkt in bookmaker['markets']:
                for outcome in mkt['outcomes']:
                    key = f"{mkt['key']}:{outcome['name']}"
                    if key not in best_odds or outcome['price'] > best_odds[key]['price']:
                        best_odds[key] = {
                            'price': outcome['price'],
                            'bookmaker': bookmaker['title'],
                            'market': mkt['key'],
                            'name': outcome['name']
                        }

        inv_probs = [1 / info['price'] for info in best_odds.values()]
        fair_prob_sum = sum(inv_probs)

        for key, info in best_odds.items():
            fair_prob = (1 / info['price']) / fair_prob_sum
            value = info['price'] * fair_prob
            if value > 1.05:
                bet_amount = calculate_bet_amount(info['price'])
                all_value_bets.append({
                    "Мач": f"{match['home_team']} vs {match['away_team']}",
                    "Пазар": f"{info['market']} – {info['name']}",
                    "Коефициент": info['price'],
                    "Залог (лв)": bet_amount,
                    "Value %": round((value - 1) * 100, 2),
                    "Букмейкър": info['bookmaker'],
                    "Час": match_time_local.strftime("%H:%M")
                })

if all_value_bets:
    df = sorted(all_value_bets, key=lambda x: -x["Value %"])
    st.dataframe(df, use_container_width=True)
else:
    st.info("Няма стойностни залози към момента.")

=== ТАБ 2: История ===

with tabs[1]: st.header("История на залози") st.write("Тук ще се показват и записват направени залози (предстои разработка).")

=== ТАБ 3: Настройки ===

with tabs[2]: st.header("Настройки") st.write("Настройки за цел, банка и поддържани пазари.")

