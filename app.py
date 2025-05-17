import streamlit as st
import pandas as pd
import requests
from predictor import predict, load_model
from train_model import train_model

API_URL = "https://api.example.com/matches"  # смени с твоя API URL
API_KEY = "ТВОЯ_API_КЛЮЧ"  # сложи своя ключ тук

def load_matches_from_api():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"date": "2025-05-17"}  # или текуща дата, ако искаш динамично

    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        matches = []
        for match in data["response"]:
            matches.append({
                "Отбор 1": match["team1_name"],
                "Отбор 2": match["team2_name"],
                "Лига": match["league_name"],
                "Коеф": match["odds_home_win"]  # или друг коефициент, който ползваш
            })
        return pd.DataFrame(matches)
    except Exception as e:
        st.error(f"Грешка при зареждане на мачове: {e}")
        return pd.DataFrame()

def main():
    st.title("🎯 Value Bets Прогнози")

    if st.button("Обучение на модел"):
        with st.spinner("Обучавам модела..."):
            train_model()
        st.success("Обучението е успешно!")

    matches_df = load_matches_from_api()
    if matches_df.empty:
        st.warning("Няма налични мачове за прогнозиране.")
        return

    st.write(f"Намерени мачове: {len(matches_df)}")
    st.dataframe(matches_df)

    try:
        results_df = predict(matches_df)
        st.write("Прогнози за Value Bets:")
        st.dataframe(results_df)
    except Exception as e:
        st.error(f"Грешка при прогнозиране: {e}")

if __name__ == "__main__":
    main()
