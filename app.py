import streamlit as st
import pandas as pd
from data_loader import load_upcoming_matches
from predictor import predict
import streamlit as st
from train_model import train

st.title("Value Bets Прогнози")

if st.button("🔄 Преобучи модела"):
    train()
    st.success("✅ Моделът и енкодерите са преобучени!")

st.title("Value Bet Predictor")

# Зареждаме предстоящите мачове
matches_df = load_upcoming_matches()

st.write("### Предстоящи мачове:")
st.dataframe(matches_df)

# Ако има мачове, правим прогноза
if not matches_df.empty:
    preds = predict(matches_df)

    # Добавяме колоната с вероятности към таблицата
    matches_df["Вероятност за value bet"] = preds

    st.write("### Прогнози:")
    st.dataframe(matches_df)
else:
    st.write("Няма налични мачове за прогноза.")
