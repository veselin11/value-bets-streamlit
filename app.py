import streamlit as st
import requests
import datetime
import time

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
    """
    Търсим мач в football-data.org по дата и отбори, връщаме резултат и статус
    """
    try:
        # Форматираме дата YYYY-MM-DD
        date_str = match_date.strftime("%Y-%m-%d")
        url = f"{FOOTBALL_DATA_BASE_URL}/matches?dateFrom={date_str}&dateTo={date_str}"

        response = requests.get(url, headers=HEADERS_FOOTBALL_DATA)
        response.raise_for_status()
        data = response.json()

        for match in data.get("matches", []):
            # Сравняваме отбори (сравнявайки с главни букви и махаме бели пространства)
            if (match["homeTeam"]["name"].strip().upper() == home_team.strip().upper() and
                match["awayTeam"]["name"].strip().upper() == away_team.strip().upper()):
                status = match["status"]  # SCHEDULED, LIVE, FINISHED
                score_home = match["score"]["fullTime"]["home"]
                score_away = match["score"]["fullTime"]["away"]
                if status == "FINISHED" and score_home is not None and score_away is not None:
                    return status, score_home, score_away
                else:
                    return status, None, None
        return None, None, None
    except Exception as e:
        st.warning(f"Грешка при заявка за резултат от football-data: {e}")
        return None, None, None

def determine_bet_outcome(market_key, selection, score_home, score_away):
    """
    Определяме печалба/загуба според пазара и избор
    """
    if score_home is None or score_away is None:
        return None  # няма резултат още

    if market_key == "h2h":
        # избор може да е името на отбор или "Draw"
        if selection == "Draw":
            return 1 if score_home == score_away else 0
        elif selection == "Overtime" or selection == "Tie":
            return 0
        else:
            if selection == "Home":
                return 1 if score_home > score_away else 0
            elif selection == "Away":
                return 1 if score_away > score_home else 0
            else:
                # Ако изборът е име на отбор, сравняваме с резултата
                if selection == match_home_team:
                    return 1 if score_home > score_away else 0
                elif selection == match_away_team:
                    return 1 if score_away > score_home else 0
                else:
                    return 0

    elif market_key == "totals":
        # selection е нещо като "Over 2.5" или "Under 3.5"
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
    else:
        return None

st.title("ТОП Стойностни Залози с Реални Резултати")

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
                        goal_line = name.split(' ')[1] if len(name.split(' ')) > 1 else ""

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

st.subheader("ТОП 10 Стойностни Залози (Непочнали)")

for bet in filtered_bets[:10]:
    # Вземаме резултат от football-data.org
    status, score_home, score_away = get_match_result_from_football_data(
        bet["home_team"], bet["away_team"], bet["match_time_obj"]
    )

    if status == "FINISHED":
        outcome = determine_bet_outcome(bet["market"], bet["selection"], score_home, score_away)
        if outcome is None:
            # няма валиден резултат за този пазар
            continue
        profit = calculate_profit(outcome, bet['odd'])
        total_bets += 1
        total_profit += profit
        if profit > 0:
            wins += 1
        else:
            losses += 1
        result_text = "Печалба" if outcome == 1 else "Загуба"
    else:
        profit = None
        result_text = "Мачът не е приключил"

    st.markdown(
        f"""
        <div style="border:1px solid #ddd; padding:10px
