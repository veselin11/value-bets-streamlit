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
    if market_key == "totals":
        parts = name.split()
        if len(parts) == 2:
            selection = parts[0]  # Over или Under
            goals = parts[1]      # 2.5, 3.0 и т.н.
            return f"{selection} {goals} гол(а)"
    return name

st.set_page_config(page_title="ТОП Стойностни Залози", layout="wide")
st.title("ТОП Стойностни Залози - Само Най-Добрите")
st.markdown("""
Избери дата за филтриране на мачове и виж стойностните залози само за непочнали събития.
""")

selected_date = st.date_input("Избери дата", datetime.datetime.utcnow().date())

value_bets = []
now = datetime.datetime.utcnow()

for league_key in EUROPE_LEAGUES:
    url = f"{BASE_URL}/{league_key}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal&dateFormat=iso"
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

                if value_percent >= 5:
                    value_bets.append({
                        "league": league_key,
                        "match": match_label,
                        "time": match_time.strftime("%Y-%m-%d %H:%M"),
                        "selection_raw": name,
                        "selection": format_selection(market_key, name),
                        "market": market_key,
                        "odd": max_odd,
                        "value": value_percent,
                        "match_time_obj": match_time
                    })
    except Exception as e:
        st.error(f"Грешка при зареждане на {league_key}: {e}")

filtered_bets = remove_duplicates_by_match(value_bets)
filtered_bets.sort(key=lambda x: x["value"], reverse=True)

st.subheader(f"ТОП 10 Стойностни Залози за {selected_date.strftime('%d.%m.%Y')} (Непочнали)")

if filtered_bets:
    if "bets_placed" not in st.session_state:
        st.session_state.bets_placed = []

    for i, bet in enumerate(filtered_bets[:10], start=1):
        with st.container():
            st.markdown(f"""
                <div style="padding:10px; border:1px solid #ddd; border-radius:8px; margin-bottom:12px;
                            background: linear-gradient(90deg, #e0f7fa 0%, #ffffff 100%);">
                    <h4 style="margin-bottom:5px;">{i}. {bet['match']} <small style="color:#888;">| {bet['time']} | {bet['league']}</small></h4>
                    <p style="margin:0; font-size:1.1em;">
                        <b>Пазар:</b> {bet['market']} &nbsp;&nbsp;
                        <b>Залог:</b> {bet['selection']} &nbsp;&nbsp;
                        <b>Коефициент:</b> {bet['odd']:.2f} &nbsp;&nbsp;
                        <b>Стойност:</b> <span style="color:green;">+{bet['value']}%</span>
                    </p>
                    <p style="margin:5px 0 0 0; color:#555;">Мачът не е започнал</p>
            """, unsafe_allow_html=True)

            if st.button(f"Заложи: {bet['selection']} на {bet['match']}", key=f"bet_{i}"):
                st.session_state.bets_placed.append(bet)
                st.success(f"Заложено: {bet['selection']} на {bet['match']} с коефициент {bet['odd']:.2f}")

            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Няма стойностни залози с достатъчно висока стойност за избраната дата.")
