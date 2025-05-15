import streamlit as st
import requests
from datetime import datetime
import pytz
import math
import pandas as pd

# Настройки
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"  # Заменете с валиден ключ, ако имате
SPORT = "soccer"
REGIONS = "eu"
MARKETS = "h2h,totals,btts"  # Добавени пазари: Над/Под и ГГ
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

# Интерфейс
st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# ============ Настройки ============
with tabs[2]:
    st.header("Настройки")
    col1, col2, col3 = st.columns(3)
    with col1:
        target_profit = st.number_input("Целева печалба (лв)", value=150)
    with col2:
        days = st.number_input("Целеви дни", value=5)
    with col3:
        bank = st.number_input("Начална банка (лв)", value=500)

    daily_profit_goal = target_profit / days
    st.info(f"Дневна цел: {round(daily_profit_goal, 2)} лв")

# ============ Прогнози ============
with tabs[0]:
    st.title("Стойностни залози – Днес")
    st.caption("Данни от OddsAPI (добавени пазари: Победа, Над/Под, Гол/Гол)")

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
                    market_name = market['key']
                    for outcome in market['outcomes']:
                        name = f"{market_name.upper()}: {outcome['name']}"
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
                    value_percent = round((value - 1) * 100, 2)
                    value_bets.append({
                        "Мач": f"{match['home_team']} vs {match['away_team']}",
                        "Пазар": name,
                        "Коефициент": info['price'],
                        "Value %": value_percent,
                        "Букмейкър": info['bookmaker'],
                        "Час": match_time_local.strftime("%H:%M"),
                        "Мач ID": f"{match['id']}_{name}"
                    })

        if value_bets:
            df = pd.DataFrame(value_bets).sort_values("Value %", ascending=False)
            df["Избери"] = False
            selected_rows = []

            st.markdown("### Стойностни залози")
            for i, row in df.iterrows():
                with st.expander(f"{row['Мач']} — {row['Пазар']}"):
                    col1, col2, col3 = st.columns([4, 2, 2])
                    with col1:
                        st.markdown(f"**Коефициент:** {row['Коефициент']}")
                        st.markdown(f"**Value %:** `{row['Value %']}`")
                        st.markdown(f"**Букмейкър:** {row['Букмейкър']}")
                        st.markdown(f"**Час:** {row['Час']}")
                    with col2:
                        selected = st.checkbox("Залагай", key=row["Мач ID"])
                        if selected:
                            selected_rows.append(row)
                    with col3:
                        stake = st.number_input(
                            label="Сума на залог (лв)",
                            key=f"stake_{row['Мач ID']}",
                            min_value=0,
                            value=int(round((daily_profit_goal / (row["Коефициент"] - 1)) / 10.0) * 10)
                        )

            if selected_rows:
                st.subheader("Избрани залози:")
                summary = []
                total_stake = 0
                for row in selected_rows:
                    stake = st.session_state.get(f"stake_{row['Мач ID']}", 0)
                    total_stake += stake
                    summary.append({
                        "Мач": row["Мач"],
                        "Пазар": row["Пазар"],
                        "Коефициент": row["Коефициент"],
                        "Value %": row["Value %"],
                        "Сума на залог": stake
                    })
                st.dataframe(pd.DataFrame(summary))
                st.success(f"Обща сума за залагане: {total_stake} лв")
        else:
            st.info("Няма стойностни залози за днес в момента.")

# ============ История ============
with tabs[1]:
    st.header("История на залози (в разработка)")
