import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import pytz

# Настройки
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
REGION = "eu"
MARKET = "h2h"
SPORT = "soccer"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Текуща дата (UTC, защото така идват данните от OddsAPI)
today = datetime.utcnow().date()

# Заглавие
st.title("Стойностни залози - ДНЕС")
st.write("Автоматично извлечени залози чрез OddsAPI")

# Функция за извличане на коефициенти от API
@st.cache_data(ttl=600)
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "markets": MARKET,
        "oddsFormat": "decimal",
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error(f"API грешка: {response.status_code}")
        return []
    return response.json()

# Извличане на коефициенти
data = get_odds()

# Обработка на данните
value_bets = []

for match in data:
    try:
        match_time = datetime.strptime(match["commence_time"], DATE_FORMAT).date()
        if match_time != today:
            continue

        teams = match["teams"]
        bookmakers = match["bookmakers"]

        for bookmaker in bookmakers:
            for market in bookmaker["markets"]:
                if market["key"] != MARKET:
                    continue

                outcomes = market["outcomes"]
                for outcome in outcomes:
                    team = outcome["name"]
                    odds = outcome["price"]

                    # Примерна value логика (фиктивна вероятност)
                    estimated_prob = 1 / odds * 0.95
                    fair_odds = 1 / estimated_prob
                    value = odds - fair_odds

                    if value > 0.2:
                        value_bets.append({
                            "Мач": f"{teams[0]} vs {teams[1]}",
                            "Избор": team,
                            "Коефициент": round(odds, 2),
                            "Value": f"{round((value / fair_odds) * 100, 1)}%",
                            "Букмейкър": bookmaker["title"],
                            "Час": match["commence_time"][11:16]
                        })
    except Exception as e:
        continue

# Показване
if value_bets:
    df = pd.DataFrame(value_bets)
    df = df.sort_values(by="Value", ascending=False)
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Няма стойностни залози за днес към момента.")
