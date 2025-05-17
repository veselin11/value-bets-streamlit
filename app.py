import streamlit as st
import pandas as pd
from api_client import get_upcoming_matches
from predictor import predict
from datetime import date

st.set_page_config(page_title="Value Bets Прогнози", layout="wide")

def main():
    st.title("🎯 Value Bets Прогнози от Реални Мачове")

    # Избор на дата
    selected_date = st.date_input("Изберете дата за мачове:", date.today())

    st.write(f"📅 Търсим мачове за дата: {selected_date}")

    # Зареждане на мачове
    matches_df = get_upcoming_matches(selected_date.strftime("%Y-%m-%d"))

    if matches_df.empty:
        st.warning("Няма достъпни мачове в момента или възникна грешка при заявката.")
        return

    # Прогноза с ML модел
    preds = predict(matches_df)

    # Добавяме колона с вероятност за value bet
    matches_df["Вероятност за value bet"] = preds

    # Филтрираме мачове с вероятност > 0.5 (примерна граница)
    value_bets_df = matches_df[matches_df["Вероятност за value bet"] > 0.5]

    if value_bets_df.empty:
        st.info("Няма намерени стойностни залози за избраната дата.")
    else:
        st.subheader("🔎 Value залози:")
        st.dataframe(value_bets_df.reset_index(drop=True))

if __name__ == "__main__":
    main()
