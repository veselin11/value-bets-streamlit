import streamlit as st
import requests
import datetime

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

def format_selection(market_key, name):
    # Ако пазар е totals, показваме Over/Under с броя голове
    if market_key == "totals":
        parts = name.split()
        if len(parts) == 2:
            selection = parts[0]  # Over или Under
            goals = parts[1]      # брой голове (2.5, 3.0 и т.н.)
            return f"{selection} {goals} гол(а)"
    return name

def is_match_started(match_time):
    now = datetime.datetime.now(datetime.timezone.utc)
    return match_time <= now

# Инициализиране на сесийната памет за залози и статистика
if "bets_placed" not in st.session_state:
    st.session_state.bets_placed = []

if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500.0  # стартова банка

if "stake" not in st.session_state:
    st.session_state.stake = 10.0  # фиксирана сума за залог

st.title("ТОП Стойностни Залози с Управление на Банка и Статистика")
st.write("Показваме само непочнали мачове с най-висока очаквана възвръщаемост.")

# Избор на дата
selected_date = st.date_input("Избери дата за филтриране на мачове", datetime.date.today())
selected_date_str = selected_date.strftime("%Y-%m-%d")

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
            # Дата на мача
            commence_time_str = match.get("commence_time", "")
            if not commence_time_str:
                continue
            # Преобразуване към datetime с таймзона
            match_time = datetime.datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))

            # Филтър по избрана дата
            if match_time.date().isoformat() != selected_date_str:
                continue

            # Проверка дали мачът не е започнал
            if is_match_started(match_time):
                continue

            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")
            match_label = f"{home_team} vs {away_team}"

            all_odds = {}
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market["key"] not in ["h2h", "totals"]:
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

                # По-строг праг за стойностни залози
                if value_percent >= 10:
                    selection_display = format_selection(market_key, name)
                    value_bets.append({
                        "league": league_key,
                        "match": match_label,
                        "time": match_time,
                        "selection": selection_display,
                        "market": market_key,
                        "odd": max_odd,
                        "value": value_percent
                    })
    except Exception as e:
        st.error(f"Грешка при зареждане на {league_key}: {e}")

# Премахване на дубли и сортиране
filtered_bets = remove_duplicates_by_match(value_bets)
filtered_bets.sort(key=lambda x: x["value"], reverse=True)

st.subheader(f"ТОП 10 Стойностни Залози за {selected_date.strftime('%d.%m.%Y')} (Непочнали)")
if filtered_bets:
    for idx, bet in enumerate(filtered_bets[:10]):
        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown(
                f"**{bet['time'].strftime('%Y-%m-%d %H:%M')} | {bet['league']}**\n"
                f"**{bet['match']}**\n"
                f"Пазар: `{bet['market']}` | Залог: **{bet['selection']}**\n"
                f"Коефициент: **{bet['odd']:.2f}** | Стойност: **+{bet['value']}%**"
            )
        with col2:
            if st.button(f"Заложи #{idx+1}"):
                # Проверка банкрол за залог
                if st.session_state.bankroll < st.session_state.stake:
                    st.warning("Недостатъчна банка за този залог!")
                else:
                    st.session_state.bankroll -= st.session_state.stake
                    st.session_state.bets_placed.append({
                        "match": bet["match"],
                        "time": bet["time"],
                        "selection": bet["selection"],
                        "odd": bet["odd"],
                        "stake": st.session_state.stake,
                        "potential_win": round(st.session_state.stake * bet["odd"], 2),
                        "result": "pending"
                    })
                    st.success(f"Заложи {st.session_state.stake} лв. на {bet['match']} - {bet['selection']}")

else:
    st.info("Няма стойностни залози с достатъчно висока стойност за избраната дата.")

# Управление на банката и залог
st.sidebar.header("Настройки на залог и банка")
stake_input = st.sidebar.number_input("Размер на залог (лв.)", min_value=1.0, max_value=1000.0, value=st.session_state.stake, step=1.0)
st.session_state.stake = stake_input

bankroll_display = st.sidebar.metric("Налична банка (лв.)", f"{st.session_state.bankroll:.2f}")

# Показване на залозите и статистиката
st.subheader("Заложени залози и статистика")

if st.session_state.bets_placed:
    for i, bet in enumerate(st.session_state.bets_placed):
        status_color = "#555555"  # за "pending"
        status_text = "Мачът не е приключил"

        if bet["result"] == "won":
            status_color = "#0f9d58"  # зелен
            status_text = "Печелен залог"
        elif bet["result"] == "lost":
            status_color = "#db4437"  # червен
            status_text = "Загубен залог"

        st.markdown(
            f"**{bet['time'].strftime('%Y-%m-%d %H:%M')}** | **{bet['match']}**\n"
            f"Залог: **{bet['selection']}** | Коефициент: **{bet['odd']:.2f}**\n"
            f"Заложена сума: {bet['stake']} лв. | Потенциален печалба: {bet['potential_win']} лв.\n"
            f"<span style='color:{status_color}; font-weight:bold;'>{status_text}</span>",
            unsafe_allow_html=True
        )
else:
    st.info("Все още няма заложени залози.")
