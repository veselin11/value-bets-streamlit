import streamlit as st
import pandas as pd
from predictor import predict

def load_matches():
    # Зареждаме мачовете от CSV (може да го замениш с API заявка)
    df = pd.read_csv("football_data.csv")
    # Внимавай: колоните трябва да са "Отбор 1", "Отбор 2", "Лига", "Коеф"
    return df

def main():
    st.title("🎯 Value Bets Прогнози")
    st.write("Получаване на предстоящи мачове и прогноза за стойностни залози")

    matches_df = load_matches()
    st.write(f"Намерени {len(matches_df)} мача")

    # Правим прогноза
    results_df = predict(matches_df)

    # Филтрираме стойностните залози (предсказани като 1)
    value_bets = results_df[results_df["ValueBet_Prediction"] == 1]

    st.subheader(f"Намерени стойностни залози: {len(value_bets)}")
    st.dataframe(value_bets[["Отбор 1", "Отбор 2", "Лига", "Коеф", "ValueBet_Probability"]])

if __name__ == "__main__":
    main()
