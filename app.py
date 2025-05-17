import streamlit as st
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# Функция за обучение на модела
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

    st.success("✅ Моделът е обучен и записан успешно!")

# Функция за зареждане на модела и енкодерите
def load_model():
    model = joblib.load("value_bet_model.pkl")
    encoders = joblib.load("label_encoders.pkl")
    return model, encoders

# Функция за предсказване
def predict(df_matches):
    model, encoders = load_model()

    df = df_matches.copy()
    df["Отбор 1"] = encoders["team1"].transform(df["Отбор 1"])
    df["Отбор 2"] = encoders["team2"].transform(df["Отбор 2"])
    df["Лига"] = encoders["league"].transform(df["Лига"])

    X = df[["Отбор 1", "Отбор 2", "Лига", "Коеф"]]
    df["Прогноза ValueBet"] = model.predict(X)
    df["Вероятност ValueBet"] = model.predict_proba(X)[:,1]

    return df

def main():
    st.title("🎯 Value Bets Прогнози")

    # Бутон за обучение
    if st.button("Обучение на модела"):
        with st.spinner("Обучение... Моля изчакайте"):
            train_model()

    # Зареждане на мачове (пример)
    # Тук трябва да сложиш твоя начин за зареждане на matches_df, примерно от API или CSV
    try:
        matches_df = pd.read_csv("matches_to_predict.csv")  # примерно
        st.write("Намерени мачове за прогнозиране:")
        st.dataframe(matches_df.head())

        if st.button("Прогноза за стойностни залози"):
            results_df = predict(matches_df)
            st.write("Прогнози:")
            st.dataframe(results_df)
    except Exception as e:
        st.error(f"Грешка при зареждане на мачове или правене на прогноза: {e}")

if __name__ == "__main__":
    main()
