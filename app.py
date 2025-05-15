import streamlit as st
import requests
import pandas as pd

API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"
REGION = "eu"
MARKETS = "h2h"
SPORT_KEY = "soccer_epl"

st.set_page_config(page_title="Стойностни залози", layout="wide")

st.title("Стойностни залози - Премачове")
st.markdown("Извличане на стойностни залози от API в реално време")

# Настройки
sport = st.selectbox("Избери първенство", ["Английска Висша лига", "Испанска Ла Лига", "Италианска Серия А"])
sport_mapping = {
    "Английска Висша лига": "soccer_epl",
    "Испанска Ла Лига": "soccer_spain_la_liga",
    "Италианска Серия А": "soccer_italy_serie_a"
}
SPORT_KEY = sport_mapping[sport]

try:
    response = requests.get(
        "https://api.the-odds-api.com/v4/sports/{}/odds".format(SPORT_KEY),
        params={
            "apiKey": API_KEY,
            "regions": REGION,
            "markets": MARKETS,
            "oddsFormat": "decimal"
        }
    )
    if response.status_code == 200:
        data = response.json()
        if not data:
            st.warning("Няма налични прогнози в момента.")
        else:
            rows = []
            for match in data:
                home_team = match["home_team"]
                away_team = match["away_team"]
                commence = match["commence_time"][:10]
                for bookmaker in match["bookmakers"]:
                    for market in bookmaker["markets"]:
                        if market["key"] == "h2h":
                            outcomes = market["outcomes"]
                            row = {
                                "Дата": commence,
                                "Домакин": home_team,
                                "Гост": away_team,
                                "Коеф. 1": outcomes[0]["price"] if len(outcomes) > 0 else None,
                                "Коеф. 2": outcomes[1]["price"] if len(outcomes) > 1 else None,
                                "Букмейкър": bookmaker["title"]
                            }
                            rows.append(row)
            df = pd.DataFrame(rows)
            st.dataframe(df)
    else:
        st.error(f"Грешка при заявката: {response.status_code}\n{response.text}")
except Exception as e:
    st.error(f"Грешка: {e}")
