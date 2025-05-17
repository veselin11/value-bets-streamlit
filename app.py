import streamlit as st
import pandas as pd
from data_loader import load_upcoming_matches
from predictor import predict, load_model

st.set_page_config(page_title="Value Bets App", layout="centered")

st.title("🎯 Стойностни залози (Value Bets)")
st.markdown("Прогнози, базирани на обучен модел. Данните са примерни.")

# Зареждане на примерни мачове
matches_df = load_upcoming_matches()
st.subheader("Предстоящи мачове")
st.dataframe(matches_df)

# Бутон за прогноза
if st.button("🔍 Прогнозирай стойностни залози"):
    try:
        preds = predict(matches_df)
        matches_df["Value вероятност"] = preds
        matches_df["Препоръка"] = matches_df["Value вероятност"].apply(lambda x: "✅ Заложи" if x > 0.5 else "❌ Пропусни")
        st.subheader("Прогноза")
        st.dataframe(matches_df)
    except Exception as e:
        st.error(f"Грешка при прогнозиране: {e}")

# Бутон за преобучаване
st.markdown("---")
if st.button("🔄 Преобучи модела"):
    try:
        import train_model
        train_model.train()
        st.success("Моделът е успешно преобучен!")
    except Exception as e:
        st.error(f"Грешка при обучението: {e}")
