import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# Конфигурация
API_TOKEN = "685e423d2d9e078e7c5f7f9439e77f7c"
BASE_URL = "https://api.football-data.org/v4"

headers = {"X-Auth-Token": API_TOKEN}

# Титла
st.set_page_config(page_title="Value Bets App", layout="wide")
st.title("Value Bets - Статистически Залози")

# Табове
tab1, tab2, tab3 = st.tabs(["Прогнози", "Резултати", "Статистика"])

# Прогнози
with tab1:
    st.subheader("Стойностни Прогнози за Днес")

    if st.button("Зареди мачовете за деня"):
        today = datetime.today().strftime('%Y-%m-%d')
        response = requests.get(
            f"{BASE_URL}/matches?dateFrom={today}&dateTo={today}", headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            if matches:
                df = pd.DataFrame([{
                    "Час": m["utcDate"][11:16],
                    "Домакин": m["homeTeam"]["name"],
                    "Гост": m["awayTeam"]["name"],
                    "Статус": m["status"],
                    "Кръг": m["matchday"]
                } for m in matches])
                st.dataframe(df)
            else:
                st.info("Няма налични мачове за днес.")
        else:
            st.error(f"Грешка при зареждане на мачове. Код: {response.status_code}")

# Резултати
with tab2:
    st.subheader("Резултати (очаква се автоматично добавяне скоро)")

# Статистика
with tab3:
    st.subheader("Обобщена статистика")
    st.info("Тук ще се визуализират: ROI, успеваемост, печалба и графики.")
