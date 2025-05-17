import streamlit as st
import datetime
from data_loader import load_matches_from_api
from predictor import predict
from train_model import train_model

BANKROLL_DEFAULT = 500  # начална банка по подразбиране

def calculate_stake(value, bankroll):
    base_stake = bankroll * 0.05  # 5% от банката максимално
    stake = base_stake * value    # пропорционално на value
    return min(stake, bankroll * 0.1)  # максимум 10% от банката

def main():
    st.sidebar.title("Настройки")
    bankroll = st.sidebar.number_input("Начална банка (лв)", value=BANKROLL_DEFAULT, step=50)
    date_to_load = st.sidebar.date_input("Дата за мачове", value=datetime.date.today())

    st.title("🎯 Value Bets Прогнози")

    if st.button("Обучение на модел"):
        with st.spinner("Обучавам модела..."):
            train_model()
        st.success("Обучението е успешно!")

    matches_df = load_matches_from_api(date_to_load)
    if matches_df.empty:
        st.warning("Няма налични мачове за прогнозиране.")
        return

    st.write(f"Намерени мачове: {len(matches_df)}")
    st.dataframe(matches_df)

    try:
        preds = predict(matches_df)
        results_df = matches_df.copy()
        results_df["value"] = preds
        results_df["Предложена сума за залог (лв)"] = results_df["value"].apply(lambda v: calculate_stake(v, bankroll))

        st.write("Прогнози за Value Bets:")
        st.dataframe(results_df)
    except Exception as e:
        st.error(f"Грешка при прогнозиране: {e}")

if __name__ == "__main__":
    main()
