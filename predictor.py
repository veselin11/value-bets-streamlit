import pandas as pd
import joblib

def predict(df):
    model = joblib.load("value_bet_model.pkl")
    encoders = joblib.load("label_encoders.pkl")

    df = df.copy()

    df["Отбор 1"] = encoders["team1"].transform(df["Отбор 1"])
    df["Отбор 2"] = encoders["team2"].transform(df["Отбор 2"])
    df["Лига"] = encoders["league"].transform(df["Лига"])

    X = df[["Отбор 1", "Отбор 2", "Лига", "Коеф"]]
    predictions = model.predict_proba(X)[:, 1]

    df["value"] = predictions
    return df[df["value"] > 0.5].sort_values(by="value", ascending=False)
