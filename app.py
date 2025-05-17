import streamlit as st
import pandas as pd
from api_client import get_upcoming_matches
from predictor import predict

st.set_page_config(page_title="Стойностни залози - футбол", layout="wide")

def main():
    st.title("Стойностни залози - футбол")

    # Зареждаме предстоящи мачове (примерно от Premier League и La Liga)
    matches_df = get_upcoming_matches()
    if matches_df.empty:
        st.warning("Не са намерени предстоящи мачове.")
        return

    st.subheader("Предстоящи мачове")
    st.dataframe(matches_df)

    # Бутони за прогнозиране
    if st.button("Прогнозирай стойностните залози"):
        try:
            preds = predict(matches_df)
            matches_df["Вероятност за value bet"] = preds
            st.success("Прогнозирането е успешно!")
            st.dataframe(matches_df)
        except Exception as e:
            st.error(f"Грешка при прогнозиране: {e}")

if __name__ == "__main__":
    main()
