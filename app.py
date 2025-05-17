import streamlit as st
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model():
    df = pd.read_csv("football_data.csv")

    enc_team1 = LabelEncoder()
    enc_team2 = LabelEncoder()
    enc_league = LabelEncoder()

    df["Отбор 1"] = enc_team1.fit_transform(df["Отбор 1"])
    df["Отбор 2"] = enc_team2.fit_transform(df["Отбор 2"])
    df["Лига"] = enc_league.fit_transform(df["Лига"])

    X = df[["Отбор 1", "Отбор 2", "Лига", "Коеф"]]
    y = df["ValueBet"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, "value_bet_model.pkl")
    joblib.dump({"team1": enc_team1, "team2": enc_team2, "league": enc_league}, "label_encoders.pkl")

    st.success("Моделът беше обучен и записан успешно!")

def main():
    st.title("🎯 Value Bets Прогнози")

    if st.button("Обучение на модела"):
        with st.spinner("Обучение на модела... Моля изчакайте"):
            train_model()

    # Тук идва твоя код за зареждане на мачове и предсказване с вече обучен модел
    # Например:
    # matches_df = зареждане_на_мачове()
    # results_df = predict(matches_df)
    # st.dataframe(results_df)

if __name__ == "__main__":
    main()
