import streamlit as st
import pandas as pd
import requests
import datetime
from predictor import predict
from train_model import train_model

API_URL = "https://api.example.com/matches"  # смени с твоя API URL
API_KEY = "685e423d2d9e078e7c5f7f9439e77f7c"

BANKROLL = 500  # начална банка, може да се направи въвеждаема

def load_matches_from_api(date):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"date": date.strftime("%Y-%m-%d")}

    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("response"):
            st.warning("Няма мачове за избраната дата.")
            return pd.DataFrame()

        matches = []
        for match in data["response"]:
            matches.append({
                "Отбор 1": match["team1_name"],
                "Отбор 2": match["team2_name"],
                "Лига": match["league_name"],
                "Коеф": match["odds_home_win"]
            })
        return pd.DataFrame(matches)
    except Exception as e:
        st.error(f"Грешка при зареждане на мачове: {e}")
        return pd.DataFrame()

def calculate_stake(value):
    base_stake = BANKROLL * 0.05  # 5% от банката максимално
    stake = base_stake * value  # пропорционално на value
    return min(stake, BANKROLL * 0.1)  # максимум 10% от банката

def main():
    st.sidebar.title("Настройки API")
    global API_URL, API_KEY
    API_URL = st.sidebar.text_input("API URL", value=API_URL)
    API_KEY = st.sidebar.text_input("API ключ", type="password", value=API_KEY)
    
    global BANKROLL
    BANKROLL = st.sidebar.number_input("Начална банка (лв)", value=500, step=50)
    
    date_to_load = st.sidebar.date_input("Дата за мачове", value=datetime.date.today())

    st.title("🎯 Value Bets Прогнози")

    if st.button("Обучение на модел"):
        with st.spinner("Обучавам модела..."):
            train_model()
        st.success("Обучението е успешно!")

    matches_df = load_matches_from_api(date_to_load)
    if matches_df.empty:
        st.warning("Няма налични мачове за прогнозиране.")
        return

    st.write(f"Намерени мачове: {len(matches_df)}")
    st.dataframe(matches_df)

    try:
        results_df = predict(matches_df)

        # Добавяме колона със сума за залог, ако има колона 'value' в резултатите
        if 'value' in results_df.columns:
            results_df['Предложена сума за залог (лв)'] = results_df['value'].apply(calculate_stake)

        st.write("Прогнози за Value Bets:")
        st.dataframe(results_df)
    except Exception as e:
        st.error(f"Грешка при прогнозиране: {e}")

if __name__ == "__main__":
    main()
