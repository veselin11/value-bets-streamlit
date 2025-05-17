import streamlit as st
import pandas as pd
from predictor import predict  # Моделът ти за прогнозиране
from api_client import get_upcoming_matches

st.set_page_config(page_title="Value Bets", layout="wide")

def main():
    st.title("🎯 Value Bets Прогнози от Реални Мачове")

    st.markdown("Получаване на предстоящи мачове от реални лиги и определяне на стойностни залози.")

    matches_df = get_upcoming_matches()

    if matches_df.empty:
        st.warning("Няма достъпни мачове в момента или възникна грешка при заявката.")
        return

    st.subheader("Предстоящи мачове:")
    st.dataframe(matches_df)

    st.subheader("🔎 Value залози:")
    try:
        preds = predict(matches_df)
        if preds.empty:
            st.info("Няма стойностни залози сред текущите мачове.")
        else:
            st.success(f"Намерени стойностни залози: {len(preds)}")
            st.dataframe(preds)
    except Exception as e:
        st.error(f"Грешка при прогнозиране: {e}")

if __name__ == "__main__":
    main()
