import streamlit as st import requests from datetime import datetime import pytz import pandas as pd

Настройки

API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8" SPORT = "soccer" REGIONS = "eu" MARKETS = "h2h,totals,btts" ODDS_FORMAT = "decimal" DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ" local_tz = pytz.timezone("Europe/Sofia")

st.set_page_config(page_title="Стойностни залози", layout="wide") tabs = st.tabs(["Прогнози", "История", "Настройки"])

Сесийно съхранение

if 'history' not in st.session_state: st.session_state.history = []

=== ТАБ 1: Прогнози ===

with tabs[0]: st.title("Стойностни залози – Реални мачове от Европа (днес)") st.caption("Данни от OddsAPI в реално време (временно симулирани)")

try:
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception("Изчерпан лимит или невалиден API ключ.")

    data = response.json()
except:
    # Симулирани данни
    data = [{
        'home_team': 'Барселона',
        'away_team': 'Реал Мадрид',
        'commence_time': datetime.utcnow().strftime(DATE_FORMAT),
        'bookmakers': [
            {
                'title': 'Bet365',
                'markets': [
                    {
                        'key': 'h2h',
                        'outcomes': [
                            {'name': 'Барселона', 'price': 2.5},
                            {'name': 'Реал Мадрид', 'price': 2.8},
                            {'name': 'Draw', 'price': 3.1}
                        ]
                    },
                    {
                        'key': 'totals',
                        'outcomes': [
                            {'name': 'Over 2.5', 'price': 2.0},
                            {'name': 'Under 2.5', 'price': 1.9}
                        ]
                    },
                    {
                        'key': 'btts',
                        'outcomes': [
                            {'name': 'Yes', 'price': 1.95},
                            {'name': 'No', 'price': 1.85}
                        ]
                    }
                ]
            }
        ]
    }]

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
            if market['key'] not in ['h2h', 'totals', 'btts']:
                continue

            best_odds = {}
            for outcome in market['outcomes']:
                name = f"{market['key'].upper()}: {outcome['name']}"
                price = outcome['price']
                best_odds[name] = {
                    'price': price,
                    'bookmaker': bookmaker['title']
                }

            inv_probs = [1 / info['price'] for info in best_odds.values()]
            fair_prob_sum = sum(inv_probs)

            for name, info in best_odds.items():
                fair_prob = (1 / info['price']) / fair_prob_sum
                value = info['price'] * fair_prob
                if value > 1.05:
                    bet_amount = round((500 * 0.03) // 10 * 10)
                    value_bets.append({
                        "Мач": f"{match['home_team']} vs {match['away_team']}",
                        "Пазар": name,
                        "Коефициент": info['price'],
                        "Букмейкър": info['bookmaker'],
                        "Value %": round((value - 1) * 100, 2),
                        "Начален час": match_time_local.strftime("%H:%M"),
                        "Сума на залог": bet_amount
                    })

if value_bets:
    df = pd.DataFrame(value_bets).sort_values(by="Value %", ascending=False)
    selected = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="bets")
    if st.button("Заложи избраните"):
        for i in selected.index:
            row = selected.loc[i]
            row_dict = row.to_dict()
            row_dict["Статус"] = "В очакване"
            row_dict["Печалба"] = 0.0
            st.session_state.history.append(row_dict)
        st.success("Залозите са добавени в историята.")
else:
    st.info("Няма стойностни залози в момента.")

=== ТАБ 2: История ===

with tabs[1]: st.header("История на залози") if len(st.session_state.history) == 0: st.info("Няма направени залози.") else: history_df = pd.DataFrame(st.session_state.history) editable_df = st.data_editor(history_df, use_container_width=True, key="history_edit")

# Преизчисление на печалби
    total_profit = 0
    for i in editable_df.index:
        row = editable_df.loc[i]
        if row["Статус"] == "Спечелен":
            profit = row["Сума на залог"] * (row["Коефициент"] - 1)
        elif row["Статус"] == "Загубен":
            profit = -row["Сума на залог"]
        else:
            profit = 0
        editable_df.at[i, "Печалба"] = round(profit, 2)
        total_profit += profit

    st.markdown(f"**Нетна печалба:** {round(total_profit,2)} лв")
    st.markdown(f"**ROI:** {round((total_profit / sum(editable_df['Сума на залог'])) * 100, 2)} %")

=== ТАБ 3: Настройки ===

with tabs[2]: st.header("Настройки") st.write("Предстоят настройки за избор на лиги, маркети, лимити и др.")

