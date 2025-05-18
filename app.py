import streamlit as st
import requests
import datetime
import pytz

# Конфигурации
THE_ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
BASE_URL = "https://api.the-odds-api.com/v4/sports/"
MARKETS = ["totals", "h2h"]
BOOKMAKERS = ["pinnacle"]
MIN_VALUE_THRESHOLD = 0.2  # 20%
INITIAL_BANKROLL = 500
BET_AMOUNT = 50
MAX_BETS_PER_DAY = 3

if 'bets' not in st.session_state:
    st.session_state.bets = []
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = INITIAL_BANKROLL
if 'total_staked' not in st.session_state:
    st.session_state.total_staked = 0
if 'total_returned' not in st.session_state:
    st.session_state.total_returned = 0

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

# Ограничение: максимум 3 залога на избраната дата
bets_today = [b for b in st.session_state.bets if b.get('date') == selected_date.isoformat()]
if len(bets_today) >= MAX_BETS_PER_DAY:
    st.warning(f"Достигнат е максимумът от {MAX_BETS_PER_DAY} залога за деня.")
    show_bets = []
else:
    # Покажи само толкова залози, че да не се надвиши лимита
    remaining = MAX_BETS_PER_DAY - len(bets_today)
    show_bets = filtered_bets[:remaining]

# Показване на стойностните залози с бутон за залагане
st.markdown(f"<h4 style='color:#008000;'>ТОП Стойностни Залози за {selected_date.strftime('%d.%m.%Y')} (Непочнали) - Макс {MAX_BETS_PER_DAY} залога</h4>", unsafe_allow_html=True)

if not show_bets:
    st.info("Няма стойностни залози или вече сте достигнали дневния лимит.")

for i, bet in enumerate(show_bets):
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
            if st.session_state.bankroll < BET_AMOUNT:
                st.error("Недостатъчна банка за този залог!")
            else:
                result = {
                    "match": bet['match'],
                    "stake": BET_AMOUNT,
                    "odds": bet['odds'],
                    "potential_win": round(BET_AMOUNT * bet['odds'], 2),
                    "result": "pending",
                    "date": selected_date.isoformat(),
                    "selection": bet['selection'],
                    "market": bet['market']
                }
                st.session_state.bets.append(result)
                st.session_state.bankroll -= BET_AMOUNT
                st.session_state.total_staked += BET_AMOUNT
        st.markdown("</div>", unsafe_allow_html=True)

# Управление на залозите - маркиране като спечелен/загубен
st.markdown("<h4 style='color:#444;'>📊 Статистика на Залозите</h4>", unsafe_allow_html=True)
if st.session_state.bets:
    for i, bet in enumerate(st.session_state.bets):
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            status = bet['result']
            st.markdown(f"""
                <div style='background:#f9f9f9;padding:10px;border-radius:10px;margin-bottom:5px;'>
                    <b>{bet['match']}</b> | Залог: {bet['stake']} лв. | Коеф: {bet['odds']} | Статус: <i>{status}</i> | Потенц. печалба: {bet['potential_win']} лв.
                </div>
            """, unsafe_allow_html=True)
        with col2:
            if status == "pending":
                if st.button("✔️ Победа", key=f"win_{i}"):
                    st.session_state.bets[i]['result'] = "win"
                    st.session_state.bankroll += bet['stake'] * bet['odds']
                    st.session_state.total_returned += bet['stake'] * bet['odds']
        with col3:
            if status == "pending":
                if st.button("❌ Загуба", key=f"loss_{i}"):
                    st.session_state.bets[i]['result'] = "loss"
                    # Загубата вече е извадена от банката при залога

else:
    st.info("Все още няма направени залози.")

# Изчисляване на ROI
if st.session_state.total_staked > 0:
    roi = (st.session_state.total_returned - st.session_state.total_staked) / st.session_state.total_staked * 100
else:
    roi = 0

st.markdown(f"<b>Оставаща банка:</b> {st.session_state.bankroll:.2f} лв.", unsafe_allow_html=True)
st.markdown(f"<b>Общо заложени:</b> {st.session_state.total_staked} лв.", unsafe_allow_html=True)
st.markdown(f"<b>Общо върнати:</b> {st.session_state.total_returned:.2f} лв.", unsafe_allow_html=True)
st.markdown(f"<b>ROI:</b> {roi:.2f} %", unsafe_allow_html=True)
