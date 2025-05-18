import streamlit as st
import requests

st.set_page_config(page_title="Стойностни залози", layout="centered")

API_KEY = "4474e2c1f44b1561daf6c481deb050cb"
SPORT_KEYS = [
    "soccer_brazil_campeonato",
    "soccer_sweden_allsvenskan",
    "soccer_usa_mls"
]

st.title("Стойностни залози (демо)")

st.write("Зареждам мачове...")

# Показваме за проверка
st.write("Активни лиги:", SPORT_KEYS)

found = False

for sport_key in SPORT_KEYS:
    st.write(f"Проверка на лига: {sport_key}")
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        res = requests.get(url, params=params)
        if res.status_code != 200:
            st.error(f"Грешка {res.status_code} за {sport_key}: {res.text}")
            continue

        matches = res.json()
        if not matches:
            st.info(f"Няма мачове в {sport_key}")
            continue

        found = True
        for m in matches:
            st.subheader(f"{m['home_team']} vs {m['away_team']}")
            st.write("Начален час:", m["commence_time"][:16].replace("T", " "))

            for bookmaker in m.get("bookmakers", []):
                st.write(f"Букмейкър: {bookmaker['title']}")
                for outcome in bookmaker["markets"][0]["outcomes"]:
                    st.write(f"{outcome['name']}: {outcome['price']}")
            st.markdown("---")

    except Exception as e:
        st.error(f"Грешка при връзка с {sport_key}: {str(e)}")

if not found:
    st.warning("Не бяха открити стойностни залози в нито една лига.")
