import streamlit as st
import requests
import datetime
import pytz
import matplotlib.pyplot as plt

# Константи
THE_ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"
MARKETS = ["totals", "h2h"]
BOOKMAKERS = ["pinnacle"]
MIN_VALUE_THRESHOLD = 0.2  # 20%
STARTING_BANKROLL = 500
TARGET_BANKROLL = 650
KELLY_FRACTION = 0.5

# Session state
if 'bets' not in st.session_state:
    st.session_state.bets = []
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = STARTING_BANKROLL
if 'daily_results' not in st.session_state:
    st.session_state.daily_results = {}

# UI
st.markdown("## 🎯 Цел: 30% печалба за 5 дни (от 500 до 650 лв.)")
selected_date = st.date_input("📅 Избери дата", value=datetime.date.today())
today_str = selected_date.strftime('%Y-%m-%d')

# Прогрес
progress = ((st.session_state.bankroll - STARTING_BANKROLL) / (TARGET_BANKROLL - STARTING_BANKROLL)) * 100
st.progress(min(progress, 100), text=f"Прогрес към целта: {progress:.1f}%")

# Функции
@st.cache_data(show_spinner=False)
def fetch_odds(sport_key):
    url = f"{BASE_URL}{sport_key}/odds"
    params = {
        "apiKey": THE_ODDS_API_KEY,
        "regions": "eu",
        "markets": ",".join(MARKETS),
        "bookmakers": ",".join(BOOKMAKERS),
        "dateFormat": "iso"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def calculate_value(odds, implied_prob):
    if odds <= 1 or implied_prob <= 0:
        return -1
    fair_odds = 1 / implied_prob
    value = (odds - fair_odds) / fair_odds
    return round(value * 100, 2)

def kelly_bet_size(bankroll, odds, implied_prob, kelly_fraction=0.5):
    if implied_prob == 0 or odds <= 1:
        return 0
    b = odds - 1
    q = 1 - implied_prob
    kelly = ((b * implied_prob - q) / b)
    return round(max(0, bankroll * kelly * kelly_fraction), 2)

# Извличане на стойностни залози
sports = ["soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_denmark_superliga"]
value_bets = []
now = datetime.datetime.now(datetime.timezone.utc)

for sport in sports:
    try:
        data = fetch_odds(sport)
        for match in data:
            match_time = datetime.datetime.fromisoformat(match['commence_time'].replace("Z", "+00:00"))
            if match_time.date() != selected_date:
                continue
            for bookmaker in match['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] not in MARKETS:
                        continue
                    for outcome in market['outcomes']:
                        if 'price' not in outcome or outcome['price'] <= 1:
                            continue
                        implied_prob = 0.5 if market['key'] == "totals" else 0.33
                        selection = outcome['name']
                        if market['key'] == "totals" and "point" in outcome:
                            selection += f" {outcome['point']} гола"

                        value = calculate_value(outcome['price'], implied_prob)
                        if value >= MIN_VALUE_THRESHOLD * 100:
                            stake = kelly_bet_size(st.session_state.bankroll, outcome['price'], implied_prob, KELLY_FRACTION)
                            if stake >= 1:
                                value_bets.append({
                                    "match": f"{match['home_team']} vs {match['away_team']}",
                                    "time": match_time,
                                    "league": sport,
                                    "market": market['key'],
                                    "selection": selection,
                                    "odds": outcome['price'],
                                    "value": value,
                                    "stake": stake
                                })
    except Exception as e:
        st.warning(f"⚠️ Грешка при зареждане на {sport}: {e}")

# Филтриране и сортиране
filtered_bets = [b for b in value_bets if b['time'] > now]
filtered_bets.sort(key=lambda x: x['value'], reverse=True)

# Показване на ТОП 3
st.markdown(f"### 🧠 ТОП 3 Стойностни Залога за {selected_date.strftime('%d.%m.%Y')}")
shown_bets = 0
for i, bet in enumerate(filtered_bets):
    if shown_bets >= 3:
        break
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
            <div style='border:1px solid #ccc; padding:10px; border-radius:10px; margin-bottom:10px;'>
                <b style='color:#444;'>{bet['time'].strftime('%H:%M')} | {bet['league']}</b><br>
                <b>{bet['match']}</b><br>
                <i>Пазар:</i> {bet['market']} | <i>Залог:</i> {bet['selection']}<br>
                <i>Коефициент:</i> <b>{bet['odds']}</b> | <i>Стойност:</i> <span style='color:#007700;'>+{bet['value']}%</span><br>
                💸 <b>Препоръчан залог:</b> {bet['stake']} лв.
            </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("Заложи", key=f"bet_{i}"):
            result = {
                "match": bet['match'],
                "stake": bet['stake'],
                "odds": bet['odds'],
                "potential_win": round(bet['stake'] * bet['odds'], 2),
                "result": "pending",
                "date": today_str
            }
            st.session_state.bets.append(result)
            st.session_state.bankroll -= bet['stake']
            shown_bets += 1

# История
st.markdown("### 📋 История на Залозите")
if st.session_state.bets:
    for bet in st.session_state.bets:
        st.markdown(f"""
            <div style='background:#f9f9f9;padding:10px;border-radius:10px;margin-bottom:5px;'>
                {bet['date']} | {bet['match']} | {bet['stake']} лв. @ {bet['odds']} | Потенц. печалба: {bet['potential_win']} | Статус: {bet['result']}
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("Няма още направени залози.")

# Графика: напредък по дни
st.markdown("### 📊 Напредък по дни")
if st.session_state.bets:
    for bet in st.session_state.bets:
        day = bet['date']
        if day not in st.session_state.daily_results:
            st.session_state.daily_results[day] = 0
        st.session_state.daily_results[day] += bet['stake']

    days = list(st.session_state.daily_results.keys())
    amounts = list(st.session_state.daily_results.values())

    fig, ax = plt.subplots()
    ax.bar(days, amounts, color="#007700")
    ax.set_ylabel("Общо заложено (лв.)")
    ax.set_title("Залози по дни")
    st.pyplot(fig)

# Текуща банка
st.markdown(f"💰 **Текуща банка:** {st.session_state.bankroll:.2f} лв.")
