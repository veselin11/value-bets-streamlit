import streamlit as st
import requests
import datetime
import pandas as pd

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"

EUROPE_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_portugal_primeira_liga",
    "soccer_sweden_allsvenskan",
    "soccer_norway_eliteserien",
    "soccer_denmark_superliga"
]

def calculate_value(odd, avg_odd):
    if not avg_odd or avg_odd == 0:
        return 0
    return round((odd - avg_odd) / avg_odd * 100, 2)

def remove_duplicates_by_match(bets):
    unique = {}
    for bet in bets:
        key = (bet['match'], bet['selection'])
        if key not in unique or unique[key]['value'] < bet['value']:
            unique[key] = bet
    return list(unique.values())

st.set_page_config(page_title="ТОП Стойностни Залози", layout="wide")
st.title("ТОП Стойностни Залози с Реални Резултати")
st.markdown("Избери дата за филтриране на мачове (само непочнали):")

# Избор на дата
selected_date = st.date_input("Дата", value=datetime.date.today(), min_value=datetime.date.today())

value_bets = []

for league_key in EUROPE_LEAGUES:
    url = f"{BASE_URL}/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal&dateFormat=iso"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        if not matches:
            continue

        for match in matches:
            match_time_str = match.get("commence_time", "")
            if not match_time_str:
                continue
            # parse datetime as aware UTC
            match_time = datetime.datetime.fromisoformat(match_time_str.replace("Z", "+00:00"))
            match_date = match_time.date()

            # Покажи само за избраната дата
            if match_date != selected_date:
                continue

            # Покажи само непочнали мачове
            now = datetime.datetime.now(datetime.timezone.utc)
            if match_time <= now:
                continue

            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_label = f"{home_team} vs {away_team}"

            all_odds = {}
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    market_key = market.get("key", "")
                    # Изключваме пазара "goal/goal" (btts)
                    if market_key == "btts":
                        continue
                    for outcome in market.get("outcomes", []):
                        selection_name = outcome.get("name", "")
                        price = outcome.get("price", 0)

                        # За пазар totals да вземем "головете" от key (напр. totals_2.5)
                        if market_key == "totals":
                            # някои пазари са totals_2.5, други само totals
                            # да вземем колко гола
                            # В някои API пазара key може да е само "totals"
                            # Понякога "key" е просто "totals", няма информация за голове, тогава няма как
                            # Нека пробваме да намерим "point" от market:
                            points = market.get("points", None)
                            # ако няма, ще търсим в ключа на market:
                            # (в този API не винаги има, затова пропускаме)
                            if points is not None:
                                goal_line = points
                            else:
                                goal_line = "n/a"
                            selection_label = f"{selection_name} {goal_line} гол(а)"
                        else:
                            selection_label = selection_name

                        key = (market_key, selection_label)
                        all_odds.setdefault(key, []).append(price)

            for (market_key, selection_label), prices in all_odds.items():
                if len(prices) < 2:
                    continue
                max_odd = max(prices)
                avg_odd = sum(prices) / len(prices)
                value_percent = calculate_value(max_odd, avg_odd)

                # Сега малко по-строги критерии за стойност:
                if value_percent >= 10 and max_odd <= 4.0:
                    value_bets.append({
                        "league": league_key,
                        "match": match_label,
                        "time": match_time.strftime("%Y-%m-%d %H:%M"),
                        "match_time_obj": match_time,
                        "selection": selection_label,
                        "market": market_key,
                        "odd": max_odd,
                        "value": value_percent
                    })

    except Exception as e:
        st.error(f"Грешка при зареждане на {league_key}: {e}")

filtered_bets = remove_duplicates_by_match(value_bets)
filtered_bets.sort(key=lambda x: x["value"], reverse=True)

st.markdown(f"## ТОП 10 Стойностни Залози за {selected_date.strftime('%d.%m.%Y')} (Непочнали)")
if filtered_bets:
    for bet in filtered_bets[:10]:
        st.markdown(
            f"""
            <div style="padding:10px; margin-bottom:10px; border-radius:8px; background: linear-gradient(90deg, #4caf50, #81c784); color: white;">
                <b>{bet['time']}</b> | <i>{bet['league']}</i><br>
                <h4 style="margin:5px 0;">{bet['match']}</h4>
                <b>Пазар:</b> {bet['market']} | <b>Избор:</b> {bet['selection']}<br>
                <b>Коефициент:</b> {bet['odd']:.2f} | <b>Стойност:</b> +{bet['value']}%<br>
                <span style="color:#eeeeee;">Мачът не е започнал</span>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("Няма стойностни залози с достатъчно висока стойност за избраната дата.")
