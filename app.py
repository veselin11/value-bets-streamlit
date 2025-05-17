import streamlit as st
from predictor import predict
from api_client import get_upcoming_matches

st.title("⚽ Value Bets Прогнози – Реални Мачове")

matches_df = get_upcoming_matches(count=10)

if matches_df.empty:
    st.warning("Няма налични мачове в момента.")
else:
    preds = predict(matches_df)
    matches_df["Value %"] = (preds - 1 / matches_df["Коеф"]) * 100
    matches_df = matches_df.sort_values(by="Value %", ascending=False)

    st.subheader("Прогнозирани Value Залози")
    st.dataframe(matches_df)
