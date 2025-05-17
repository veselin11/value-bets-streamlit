import joblib
import pandas as pd

def load_model():
    model = joblib.load("value_bet_model.pkl")
    encoders = joblib.load("label_encoders.pkl")
    return model, encoders

def prepare_features(df, encoders):
    df = df.copy()
    df["Отбор 1"] = encoders["team1"].transform(df["Отбор 1"])
    df["Отбор 2"] = encoders["team2"].transform(df["Отбор 2"])
    df["Лига"] = encoders["league"].transform(df["Лига"])
    return df

def implied_probability(odds):
    try:
        return 1 / float(odds)
    except Exception:
        return 0

def predict(df):
    model, encoders = load_model()
    X = prepare_features(df, encoders)
    preds = model.predict_proba(X)[:, 1]  # вероятност за клас 1 (value bet)

    df = df.copy()
    df["predicted_prob"] = preds
    df["implied_prob"] = df["Коеф"].apply(implied_probability)
    df["value"] = df["predicted_prob"] - df["implied_prob"]

    # Филтриране само на положителни value залози
    value_bets_df = df[df["value"] > 0].copy()

    # Сортираме по стойност value desc
    value_bets_df = value_bets_df.sort_values(by="value", ascending=False)

    return value_bets_df.reset_index(drop=True)
