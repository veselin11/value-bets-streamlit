import streamlit as st import requests from datetime import datetime import pytz

=== Настройки и API ===

API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8" SPORT = "soccer" REGIONS = "uk,us,eu,au" MARKETS = "h2h" ODDS_FORMAT = "decimal" DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ" local_tz = pytz.timezone("Europe/Sofia")

=== Streamlit Setup ===

st.set_page_config(page_title="Стойностни залози", layout="wide") st.title("Стойностни залози – Реални мачове от Европа (днес)")

=== Session State ===

if "history" not in st.session_state: st.session_state.history = []

=== Заявка към API ===

url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds" params = { "apiKey": API_KEY, "regions": REGIONS, "markets": MARKETS, "oddsFormat": ODDS_FORMAT }

response = requests.get(url, params=params)

if response.status_code != 200: st.error(f"Грешка при зареждане на данни: {response.status_code} - {response.text}") else: data = response.json() value_bets = []

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
                "Начален час": match_time_local.strftime("%H:%M")
            })

if value_bets:
    df = sorted(value_bets, key=lambda x: -x["Value %"])
    st.table(df)
else:
    st.info("Няма стойностни залози за днешните мачове в момента.")

