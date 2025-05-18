import streamlit as st
import requests
import datetime

ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
FOOTBALL_DATA_API_KEY = "e004e3601abd4b108a653f9f3a8c5ede"
ODDS_BASE_URL = "https://api.the-odds-api.com/v4/sports"
FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"

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

BET_AMOUNT = 10  # лв. на залог

HEADERS_FOOTBALL_DATA = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}

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

def calculate_profit(bet_outcome, odd, amount=BET_AMOUNT):
    if bet_outcome == 1:  # печеливш залог
        return round(amount * odd - amount, 2)
    else:
        return -amount

def get_match_result_from_football_data(home_team, away_team, match_date):
    try:
        date_str = match_date.strftime("%Y-%m-%d")
        url = f"{FOOTBALL_DATA_BASE_URL}/matches?dateFrom={date_str}&dateTo={date_str}"

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

def determine_bet_outcome(market_key, selection, score_home, score_away, home_team, away_team):
    if score_home is None or score_away is None:
        return None

    if market_key == "h2h":
        if selection == "Draw":
            return 1 if score_home == score_away else 0
        elif selection == home_team:
            return 1 if score_home > score_away else 0
        elif selection == away_team:
            return 1 if score_away > score_home else 0
        else:
            return 0

    elif market_key == "totals":
        parts = selection.split(' ')
        if len(parts) == 2:
            direction, goal_line_str = parts
            try:
                goal_line = float(goal_line_str)
                total_goals = score_home + score_away
                if direction.lower() == "over":
                    return 1 if total_goals > goal_line else 0
                elif direction.lower() == "under":
                    return 1 if total_goals < goal_line else 0
            except:
                return 0
        return 0

    return None

# --- UI ---

st.set_page_config(page_title="Стойностни залози", layout="wide")
st.title("ТОП Стойностни Залози с Реални Резултати")

# Избор на дата
selected_date = st.date_input("Избери дата за филтриране на мачове", datetime.date.today())

value_bets = []
now = datetime.datetime.now(datetime.timezone.utc)

for league_key in EUROPE_LEAGUES:
    url = f"{ODDS_BASE_URL}/{league_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal&dateFormat=iso"
    try:
        response = requests.get(url)
        response.raise_for_status()
        matches = response.json()
        if not matches:
            continue

        for match in matches:
            match_time = datetime.datetime.fromisoformat(match.get("commence_time", "").replace("Z", "+00:00"))
            if match_time.date() != selected_date:
                continue
            if match_time <= now:
                continue  # само непочнали

            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_label = f"{home_team} vs {away_team}"

            all_odds = {}
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] == "btts":
                        continue
                    for outcome in market.get("outcomes", []):
                        key = (market["key"], outcome["name"])
                        all_odds.setdefault(key, []).append(outcome["price"])

            for (market_key, name), prices in all_odds.items():
                if len(prices) < 2:
                    continue
                max_odd = max(prices)
                avg_odd = sum(prices) / len(prices)
                value_percent = calculate_value(max_odd, avg_odd)

                if value_percent >= 5:
                    goal_line = ""
                    if market_key == "totals":
                        # Взимаме числото след "Over " или "Under "
                        parts = name.split(' ')
                        if len(parts) > 1:
                            goal_line = parts[1]

                    value_bets.append({
                        "league": league_key,
                        "match": match_label,
                        "time": match_time.strftime("%Y-%m-%d %H:%M"),
                        "selection": name,
                        "market": market_key,
                        "odd": max_odd,
                        "value": value_percent,
                        "goal_line": goal_line,
                        "home_team": home_team,
                        "away_team": away_team,
                        "match_time_obj": match_time
                    })

    except Exception as e:
        st.error(f"Грешка при зареждане на {league_key}: {e}")

filtered_bets = remove_duplicates_by_match(value_bets)
filtered_bets.sort(key=lambda x: x["value"], reverse=True)

total_bets = 0
total_profit = 0
wins = 0
losses = 0

st.subheader(f"ТОП 10 Стойностни Залози за {selected_date.strftime('%d.%m.%Y')} (Непочнали)")

for bet in filtered_bets[:10]:
    status, score_home, score_away = get_match_result_from_football_data(
        bet["home_team"], bet["away_team"], bet["match_time_obj"]
    )

    if status == "FINISHED":
        outcome = determine_bet_outcome(bet["market"], bet["selection"], score_home, score_away, bet["home_team"], bet["away_team"])
        if outcome is None:
            continue
        profit = calculate_profit(outcome, bet['odd'])
        total_bets += 1
        total_profit += profit
        if profit > 0:
            wins += 1
        else:
            losses += 1
        result_text = "Печалба" if outcome == 1 else "Загуба"
        result_color = "#1a7f37" if outcome == 1 else "#cc0000"
    else:
        profit = None
        result_text = "Мачът не е приключил"
        result_color = "#555555"

    # Цветно и стилно каре
    st.markdown(f"""
        <div style="
            border:1px solid #ddd; 
            padding:12px; 
            margin-bottom:12px; 
            border-radius:8px; 
            box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
            background: linear-gradient(90deg, #f9f9f9 0%, #e6f0ff 100%);
            font-family: Arial, sans-serif;
        ">
            <b style="font-size:1.1em; color:#333;">{bet['time']} | {bet['league']}</b><br>
            <span style="font-size:1.2em; font-weight:600; color:#222;">{bet['match']}</span><br><br>
            Пазар: <i style="color:#555;">{bet['market']}</i> | Избор: <b style="color:#004080;">{bet['selection']}</b><br>
            Коефициент: <b style="color:#004080;">{bet['odd']}</b> | Стойност: <b style="color:#0066cc;">{bet['value']}%</b><br>
            {(f"<span style='color:#333;'>Гол линия: <b>{bet['goal_line']}</b></span><br>" if bet['goal_line'] else "")}
            Статус: <b style="color:{result_color};">{result_text}</b>
            {f"| Печалба/Загуба: <b style='color:{result_color};'>{profit} лв.</b>" if profit is not None else ''}
        </div>
    """, unsafe_allow_html=True)

if total_bets > 0:
    st.markdown(f"""
        <div style="font-family: Arial, sans-serif; margin-top:20px;">
            <b>Общо проверени залози:</b> {total_bets} &nbsp;&nbsp;|&nbsp;&nbsp; 
            <b style="color:#0066cc;">Печалба/Загуба общо:</b> {total_profit} лв.<br>
            <b style="color:#1a7f37;">Печеливши:</b> {wins} &nbsp;&nbsp;|&nbsp;&nbsp; 
            <b style="color:#cc0000;">Загубени:</b> {losses}
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("Няма стойностни залози за избраната дата и критерии.")
