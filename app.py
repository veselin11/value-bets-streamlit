import streamlit as st
import pandas as pd
from data_loader import load_upcoming_matches
from predictor import load_model, load_encoders, predict_probabilities

# Настройки на приложението
st.set_page_config(page_title="Value Bets", layout="wide")
st.title("🎯 Стойностни Залози")

# Зареждане на мачове и модел
matches = load_upcoming_matches()
model = load_model()
encoders = load_encoders()

# Бутон за изчисляване на стойностни залози
if st.button("🔍 Покажи стойностни прогнози"):
    rows = []

    for _, row in matches.iterrows():
        df_match = pd.DataFrame([row])  # Преобразуваме реда в DataFrame
        probs = predict_probabilities(model, df_match, encoders)

        model_prob = probs[0][1]  # Пример: вероятност за победа на Отбор 1
        implied_prob = 1 / row["Коеф"]
        value_pct = (model_prob - implied_prob) * 100

        rows.append({
            "Мач": f"{row['Отбор 1']} - {row['Отбор 2']}",
            "Коеф": row["Коеф"],
            "Шанс (модел)": f"{model_prob*100:.1f}%",
            "Имплицитен шанс": f"{implied_prob*100:.1f}%",
            "Value %": f"{value_pct:.2f}"
        })

    df_out = pd.DataFrame(rows)
    df_out = df_out.sort_values(by="Value %", ascending=False)
    st.dataframe(df_out, use_container_width=True)
