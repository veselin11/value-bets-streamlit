import streamlit as st
import requests
from datetime import datetime
import pytz

# API настройки
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
SPORT = "soccer"
REGIONS = "uk,us,eu,au"
MARKETS = "h2h,totals,btts"  # Добавих нови пазари
ODDS_FORMAT = "decimal"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
local_tz = pytz.timezone("Europe/Sofia")

# Инициализация на данни за история
if 'history' not in st.session_state:
    st.session_state.history = []

# Функция за изчисляване на стойност на залога
def calculate_bet_amount(bankroll, target_profit):
    return round(target_profit / 2, -1)  # Кръгли на 10

# Функция за добавяне на залог в историята
def add_bet_to_history(match, bet_type, odds, bet_amount, status, profit):
    st.session_state.history.append({
        "Мач": f"{match['home_team']} vs {match['away_team']}",
        "Пазар": bet_type,
        "Коефициент": odds,
        "Сума на залог": bet_amount,
        "Статус": status,
        "Печалба": profit
    })

# === ТАБ 1: Прогнози ===
tabs = st.tabs(["Прогнози", "История", "Настройки"])

with tabs[0]:
    st.title("Стойностни залози – Реални мачове от Европа (днес)")
    st.caption("Данни от OddsAPI в реално време")

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
                    if market['key'] in ['h2h', 'totals', 'btts']:  # Проверявам за допълнителни пазари
                        for outcome in market['outcomes']:
                            name = outcome['name']
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
                    value_bets.append({
                        "Мач": f"{match['home_team']} vs {match['away_team']}",
                        "Пазар": name,
                        "Коефициент": info['price'],
                        "Букмейкър": info['bookmaker'],
                        "Value %": round((value - 1) * 100, 2),
                        "Начален час": match_time_local.strftime("%H:%M")
                    })

        if value_bets:
            df = sorted(value_bets, key=lambda x: -x["Value %"])
            # Въвеждаме целта и стойността на залога
            target_profit = st.number_input("Цел за печалба", min_value=0, value=100, step=10)
            bankroll = st.number_input("Начална банка", min_value=0, value=500, step=10)
            bet_amount = calculate_bet_amount(bankroll, target_profit)
            st.write(f"Залог за мач: {bet_amount} лв")
            
            # Създаване на таблица със стойностни залози и възможност за добавяне в историята
            for idx, row in enumerate(df):
                with st.expander(f"Залог: {row['Мач']}"):
                    if st.button(f"Заложи на {row['Мач']} ({row['Пазар']})", key=idx):
                        # При натискане добавяме в историята
                        add_bet_to_history(row, row["Пазар"], row["Коефициент"], bet_amount, "В процес", 0)
                        st.success(f"Залогът е добавен към историята.")

            st.dataframe(df, use_container_width=True)
        else:
            st.info("Няма стойностни залози за днешните мачове в момента.")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залози")

    if len(st.session_state.history) > 0:
        history_df = pd.DataFrame(st.session_state.history)
        
        # Оцветяване на редовете в зависимост от статуса
        def highlight_status(val):
            color = 'green' if val == "Спечелен" else ('red' if val == "Загубен" else 'yellow')
            return f'background-color: {color}'
        
        st.dataframe(history_df.style.applymap(highlight_status, subset=["Статус"]), use_container_width=True)
    else:
        st.write("Няма записани залози.")
    
# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки")
    st.write("Предстоят настройки за избор на лиги, маркети, лимити и др.")
