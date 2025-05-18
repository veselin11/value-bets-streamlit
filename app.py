import streamlit as st
import requests
from datetime import date

API_KEY = "cb4a5917231d8b20dd6b85ae9d025e6e"
BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}

# Инициализиране на сесията за банка и история
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 500.0
if "bets_history" not in st.session_state:
    st.session_state.bets_history = []

def get_fixtures_for_today():
    today_str = date.today().isoformat()
    url = f"{BASE_URL}/fixtures"
    params = {"date": today_str}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if data["results"] == 0:
        return []
    return data["response"]

def display_bets():
    st.header("Днешни футболни мачове и коефициенти")

    fixtures = get_fixtures_for_today()
    if not fixtures:
        st.write("Няма мачове за днес или проблем с API.")
        return

    for idx, fixture in enumerate(fixtures):
        league = fixture["league"]["name"]
        home = fixture["teams"]["home"]["name"]
        away = fixture["teams"]["away"]["name"]
        match_time = fixture["fixture"]["date"][11:16]  # час и минути
        odds_data = fixture.get("odds")
        
        # Ако няма odds в отговора, пропускаме (API понякога не връща)
        bookmakers = fixture.get("bookmakers", [])
        # Намираме първия букмейкър с коефициенти (ако има)
        odds = None
        if bookmakers:
            markets = bookmakers[0].get("bets", [])
            for bet in markets:
                if bet["name"] == "Match Winner":
                    # Взимаме 3 варианта: 1, X, 2
                    outcomes = bet.get("values", [])
                    odds = {out["name"]: out["odd"] for out in outcomes}
                    break
        
        st.markdown(f"**{league}** | {match_time} | {home} - {away}")

        if odds:
            st.write(f"Коефициенти: 1: {odds.get('1', 'н/д')} | X: {odds.get('X', 'н/д')} | 2: {odds.get('2', 'н/д')}")
            bet_option = st.radio(f"Избери прогноза за {home} - {away}:", options=["1", "X", "2"], key=f"bet_{idx}")
            bet_amount = st.number_input(f"Заложи сума за {home} - {away}:", min_value=1.0, max_value=st.session_state.bankroll, value=10.0, step=1.0, key=f"amount_{idx}")

            if st.button(f"Заложи на {home} - {away}", key=f"btn_{idx}"):
                odd_value = odds.get(bet_option)
                if odd_value:
                    # Прост модел за печалба (рандом тук, може да се доразвие)
                    import random
                    win = random.random() < 1 / float(odd_value)
                    result = "Печалба" if win else "Загуба"
                    if win:
                        profit = bet_amount * (float(odd_value) - 1)
                        st.session_state.bankroll += profit
                    else:
                        st.session_state.bankroll -= bet_amount
                    
                    st.session_state.bets_history.append({
                        "match": f"{home} - {away}",
                        "prediction": bet_option,
                        "odds": odd_value,
                        "amount": bet_amount,
                        "result": result
                    })
                    st.success(f"Резултат: {result}. Текуща банка: {st.session_state.bankroll:.2f} лв.")
                else:
                    st.error("Няма наличен коефициент за тази прогноза.")

        else:
            st.write("Коефициенти не са налични за този мач.")

    st.header("История на залозите")
    for bet in st.session_state.bets_history:
        st.write(f"{bet['match']} | Прогноза: {bet['prediction']} | Коефициент: {bet['odds']} | Сума: {bet['amount']} | Резултат: {bet['result']}")

    st.markdown(f"### Текуща банка: {st.session_state.bankroll:.2f} лв.")

if __name__ == "__main__":
    st.title("Value Bets App - Стойностни залози")
    display_bets()
