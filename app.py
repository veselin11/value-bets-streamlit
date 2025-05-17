import streamlit as st
from data_loader import load_upcoming_matches
from predictor import load_model, predict_value_bet
import pandas as pd

st.title("Value Bet Predictor")

model = load_model()
matches = load_upcoming_matches()

st.header("Предстоящи мачове")
st.dataframe(matches)

if st.button("Прогнозирай стойностните залози"):
    preds = predict_value_bet(model, matches)
    matches["Вероятност за печалба"] = preds
    st.dataframe(matches)
