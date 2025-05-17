import streamlit as st
import pandas as pd
from predictor import predict
from api_client import get_upcoming_matches

st.title("Value Bet Predictor - Реални Футболни Мачове")

# Зареждаме мачовете от API-то
try:
    matches_df = get_upcoming_matches()
except Exception as e:
    st.error(f"Грешка при зареждане на мачове: {e}")
    matches_df = pd.DataFrame()

if not matches_df.empty:
    st.write("Предстоящи мачове:")
    st.dataframe(matches_df)

    # Предсказване на вероятности за value bet
    try:
        preds = predict(matches_df)
        matches_df["Вероятност за value bet"] = preds
        st.write("Мачове с вероятности за value bet:")
        st.dataframe(matches_df.sort_values(by="Вероятност за value bet", ascending=False))
    except Exception as e:
        st.error(f"Грешка при прогнозиране: {e}")
else:
    st.info("Няма налични мачове за показване.")
