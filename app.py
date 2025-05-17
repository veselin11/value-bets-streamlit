import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import os

# --- Функция за зареждане на мачове от API ---
def get_upcoming_matches(date: str):
    API_KEY = os.getenv("API_KEY")  # Прочита API ключ от средата
    if not API_KEY:
        st.error("Не е зададен API_KEY в средата на изпълнение!")
        return pd.DataFrame()

    BASE_URL = "https://v3.football.api-sports.io"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "v3.football.api-sports.io"
    }
    url = f"{BASE_URL}/fixtures?date={date}"
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        st.error(f"Грешка при заявка към API: {res.status_code}")
        return pd.DataFrame()

    data = res.json()
    matches = []
    for match in data.get("response", []):
        try:
            matches.append({
                "Отбор 1": match["teams"]["home"]["name"],
                "Отбор 2": match["teams"]["away"]["name"],
                "Лига": match["league"]["name"],
                "Дата": match["fixture"]["date"][:10],
                "Коеф. (фиктивен)": 2.5  # може да добавиш реални коефициенти
            })
        except Exception as e:
            continue
    return pd.DataFrame(matches)

# --- Streamlit app ---
st.set_page_config(page_title="Value Bets App", layout="wide")
st.title("Value Bets - Стойностни Залози")

tab1, tab2, tab3 = st.tabs(["Прогнози", "Резултати", "Статистика"])

with tab1:
    st.subheader("Стойностни Прогнози за Днес")
    if st.button("Зареди мачовете за днес"):
        today = datetime.today().strftime("%Y-%m-%d")
        df_matches = get_upcoming_matches(today)
        if df_matches.empty:
            st.info("Няма налични мачове за днес или грешка при зареждане.")
        else:
            st.dataframe(df_matches)

with tab2:
    st.subheader("Резултати (в бъдеще)")

with tab3:
    st.subheader("Обобщена статистика")
    st.info("Тук ще се визуализират: ROI, успеваемост, печалба и графики.")
