import streamlit as st
import requests
from datetime import datetime
import pandas as pd

# Конфигурация на API
API_TOKEN = "685e423d2d9e078e7c5f7f9439e77f7c"
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_TOKEN}

st.set_page_config(page_title="Value Bets App", layout="wide")
st.title("Value Bets - Статистически Залози")

tab1, tab2, tab3 = st.tabs(["Прогнози", "Резултати", "Статистика"])

# === ТАБ 1: Прогнози ===
with tab1:
    st.subheader("Стойностни Прогнози за Днес")

    if st.button("Зареди мачовете за деня"):
        today = datetime.today().strftime('%Y-%m-%d')
        response = requests.get(f"{BASE_URL}/matches?dateFrom={today}&dateTo={today}", headers=headers)

        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])

            if matches:
                # Преобразуване в DataFrame
                df = pd.DataFrame([{
                    "Час": m["utcDate"][11:16],
                    "Домакин": m["homeTeam"]["name"],
                    "Гост": m["awayTeam"]["name"],
                    "Статус": m["status"],
                    "Кръг": m["matchday"],
                    "Фиктивен коефициент Домакин": 2.0 + (i % 3)*0.3,   # примерни фиктивни коефициенти
                    "Фиктивен коефициент Равен": 3.0 + (i % 2)*0.2,
                    "Фиктивен коефициент Гост": 2.5 + (i % 4)*0.4
                } for i, m in enumerate(matches)])

                # Филтриране по статус
                filter_status = st.multiselect(
                    "Филтрирай по статус:",
                    options=df["Статус"].unique(),
                    default=df["Статус"].unique()
                )
                filtered_df = df[df["Статус"].isin(filter_status)]

                st.dataframe(filtered_df)
            else:
                st.info("Няма налични мачове за днес.")
        else:
            st.error(f"Грешка при зареждане на мачове. Код: {response.status_code}")

# === ТАБ 2: Резултати ===
with tab2:
    st.subheader("Резултати (очаква се автоматично добавяне скоро)")
    st.info("Тук ще се показват резултатите от изиграни мачове.")

# === ТАБ 3: Статистика ===
with tab3:
    st.subheader("Обобщена статистика")
    st.info("Тук ще се визуализират: ROI, успеваемост, печалба и графики.")
