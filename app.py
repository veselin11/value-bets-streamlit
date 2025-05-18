import streamlit as st
import requests
import datetime
from functools import lru_cache

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports"
FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
HEADERS_FOOTBALL_DATA = {"X-Auth-Token": "e004e3601abd4b108a653f9f3a8c5ede"}  # <- сложи си своя ключ тук

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

@lru_cache(maxsize=50)
def get_match_result_from_football_data_cached(home_team, away_team, match_date_str):
    try:
        url = f"{FOOTBALL_DATA_BASE_URL}/matches?dateFrom={match_date_str}&dateTo={match_date_str}"
        response = requests.get(url, headers=HEADERS_FOOTBALL_DATA)
        response.raise_for_status()
        data = response.json()
        for match in data.get("matches", []):
            if (match["homeTeam"]["name"].strip().upper() == home_team.strip().upper() and
                match["awayTeam"]["name"].strip().upper() == away_team.strip().upper()):
                status = match["status"]
                score_home = match["score"]["fullTime"]["home"]
                score_away = match["score"]["fullTime"]["away"]
                if status == "FINISHED" and score_home is not None and score_away is not None:
                    return status, score_home, score_away
                else:
                    return status, None, None
        return None, None, None
    except Exception as e:
        st.warning(f"Грешка при заявка за резултат: {e}")
        return None, None, None

st.set_page_config(page_title="ТОП Стойностни Залози с Реални Резултати", layout="wide")
st.title("ТОП Стойностни Залози с Реални Резултати")

# Избор на дата
selected_date = st.date_input("Избери дата за филтриране на мачове", datetime.date.today())
selected_date_str = selected_date.strftime("%Y-%m-%d")

now = datetime.datetime.utcnow()

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
            # Филтриране по дата
            match_time = datetime.datetime.fromisoformat(match.get("commence_time", "").replace("Z", "+00:00"))
            match_date_only = match_time.date()
            if match_date_only != selected_date:
                continue  # показваме само избраната дата

            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_label = f"{home_team} vs {away_team}"

            # Събиране на всички коефициенти за всяка селекция
            all_odds = {}
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] not in ["h2h", "totals"]:
                        continue  # махаме BTTS пазара (гол/гол)

                    for outcome in market.get("outcomes", []):
                        key = (market["key"], outcome["name"])
                        # За totals пазара - добавяме info за гола (Over 2.5 например)
                        if market["key"] == "totals":
                            # Добави към името info за гола, ако има
                            line = market.get("line", None)
                            if line is not None:
                                # outcome["name"] е "Over" или "Under"
                                selection_name = f"{outcome['name']} {line}"
                            else:
                                selection_name = outcome["name"]
                        else:
                            selection_name = outcome["name"]
                        all_odds.setdefault((market["key"], selection_name), []).append(outcome["price"])

            for (market_key, selection_name), prices in all_odds.items():
                if len(prices) < 2:
                    continue
                max_odd = max(prices)
                avg_odd = sum(prices) / len(prices)
                value_percent = calculate_value(max_odd, avg_odd)

                # По-строги критерии, за да са залозите по-реалистични
                # например стойност поне 10% и коефициент между 1.4 и 3.5
                if value_percent >= 10 and 1.4 <= max_odd <= 3.5:
                    value_bets.append({
                        "league": league_key,
                        "match": match_label,
                        "time": match_time.strftime("%Y-%m-%d %H:%M"),
                        "match_time_obj": match_time,
                        "home_team": home_team,
                        "away_team": away_team,
                        "selection": selection_name,
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
        match_started = bet["match_time_obj"] <= now
        # Проверяваме резултата само ако мачът е започнал
        if match_started:
            status, score_home, score_away = get_match_result_from_football_data_cached(
                bet["home_team"], bet["away_team"], bet["match_time_obj"].strftime("%Y-%m-%d")
            )
        else:
            status, score_home, score_away = None, None, None

        if status == "FINISHED" and score_home is not None and score_away is not None:
            result_text = f"<b style='color:green;'>Резултат: {score_home} - {score_away} (КРАЙ)</b>"
        elif status in ["IN_PLAY", "PAUSED"]:
            result_text = f"<b style='color:orange;'>Мачът е в ход</b>"
        else:
            result_text = f"<b style='color:#555555;'>Мачът не е приключил</b>"

        st.markdown(
            f"""
            <div style='border:1px solid #ddd; padding:15px; margin-bottom:10px; border-radius:8px; background:#f9f9f9;'>
            <h4 style='margin-bottom:5px;'>{bet['match']} <span style='font-size:14px; color:#888;'>({bet['time']})</span></h4>
            <p style='margin:3px 0;'><b>Лига:</b> <code>{bet['league']}</code></p>
            <p style='margin:3px 0;'><b>Пазар:</b> <code>{bet['market']}</code> | <b>Залог:</b> <span style='color:#1E90FF;'>{bet['selection']}</span></p>
            <p style='margin:3px 0;'><b>Коефициент:</b> <span style='color:#007700;'>{bet['odd']:.2f}</span> | <b>Стойност:</b> <span style='color:#dd4b39;'>+{bet['value']}%</span></p>
            <p style='margin:3px 0;'>{result_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("Няма стойностни залози с достатъчно висока стойност за избраната дата.")
