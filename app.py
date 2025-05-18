import streamlit as st
import requests
import datetime
import pytz

# Конфигурации
THE_ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
FOOTBALL_DATA_API_KEY = "e004e3601abd4b108a653f9f3a8c5ede"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"
MARKETS = ["totals", "h2h"]
BOOKMAKERS = ["pinnacle"]
MIN_VALUE_THRESHOLD = 0.2  # 20%
INITIAL_BANKROLL = 1000
BET_AMOUNT = 50

if 'bets' not in st.session_state:
    st.session_state.bets = []
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = INITIAL_BANKROLL

# UI - Заглавие и избор на дата
st.markdown("""
    <h2 style='color:#004488;'>ТОП Стойностни Залози - Само Най-Добрите</h2>
    <p>Избери дата за филтриране на мачове и виж стойностните залози само за непочнали събития.</p>
""", unsafe_allow_html=True)

selected_date = st.date_input("Избери дата", value=datetime.date.today())

# Функция за зареждане на odds
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

# Изчисляване на стойност

def calculate_value(odds, implied_prob):
    if odds <= 1:
        return -1
    fair_odds = 1 / implied_prob
    value = (odds - fair_odds) / fair_odds
    return round(value * 100, 2)

# Зареждане и филтриране
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
                        if market['key'] == 'totals':
                            total = outcome.get('point')
                            selection = f"{outcome['name']} {total} гол(а)" if total else outcome['name']
                            implied_prob = 0.5
                        else:
                            selection = outcome['name']
                            implied_prob = 0.33

                        value = calculate_value(outcome['price'], implied_prob)
                        if value >= MIN_VALUE_THRESHOLD * 100:
                            value_bets.append({
                                "match": f"{match['home_team']} vs {match['away_team']}",
                                "time": match_time,
                                "league": sport,
                                "market": market['key'],
                                "selection": selection,
                                "odds": outcome['price'],
                                "value": value
                            })
    except Exception as e:
        st.warning(f"Грешка при зареждане на {sport}: {e}")

# Филтрирай по непочнали
filtered_bets = [b for b in value_bets if b['time'] > now]

# Сортирай по стойност
filtered_bets.sort(key=lambda x: x['value'], reverse=True)

# Показване на топ 10
st.markdown(f"<h4 style='color:#008000;'>ТОП 10 Стойностни Залози за {selected_date.strftime('%d.%m.%Y')} (Непочнали)</h4>", unsafe_allow_html=True)
if not filtered_bets:
    st.info("Няма стойностни залози с достатъчно висока стойност за избраната дата.")

for i, bet in enumerate(filtered_bets[:10]):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
            <div style='border:1px solid #ccc; padding:10px; border-radius:10px; margin-bottom:10px;'>
                <b style='color:#444;'>{bet['time'].strftime('%Y-%m-%d %H:%M')} | {bet['league']}</b><br>
                <b style='color:#000;'>{bet['match']}</b><br>
                <i>Пазар:</i> {bet['market']} | <i>Залог:</i> {bet['selection']}<br>
                <i>Коефициент:</i> <b>{bet['odds']}</b> | <i>Стойност:</i> <span style='color:#007700;'>+{bet['value']}%</span><br>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("Заложи", key=f"bet_{i}"):
            result = {
                "match": bet['match'],
                "stake": BET_AMOUNT,
                "odds": bet['odds'],
                "potential_win": round(BET_AMOUNT * bet['odds'], 2),
                "result": "pending"
            }
            st.session_state.bets.append(result)
            st.session_state.bankroll -= BET_AMOUNT
        st.markdown("</div>", unsafe_allow_html=True)

# Статистика на залозите
st.markdown("<h4 style='color:#444;'>📊 Статистика на Залозите</h4>", unsafe_allow_html=True)
if st.session_state.bets:
    for bet in st.session_state.bets:
        st.markdown(f"""
            <div style='background:#f9f9f9;padding:10px;border-radius:10px;margin-bottom:5px;'>
                {bet['match']} | Коеф: {bet['odds']} | Статус: {bet['result']} | Потенц. печалба: {bet['potential_win']} лв.
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("Все още няма направени залози.")

st.markdown(f"<b>Оставаща банка:</b> {st.session_state.bankroll:.2f} лв.")
