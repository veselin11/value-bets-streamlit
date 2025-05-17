import pandas as pd
import joblib

def predict(matches_df):
    model = joblib.load("value_bet_model.pkl")
    encoders = joblib.load("label_encoders.pkl")

    # Копие, за да запазим оригиналните имена
    df = matches_df.copy()

    # Добавяне на липсващи етикети към енкодерите
    def extend_encoder(encoder, values):
        known = set(encoder.classes_)
        unknown = set(values) - known
        if unknown:
            encoder.classes_ = list(encoder.classes_) + list(unknown)
        return encoder

    enc_team1 = extend_encoder(encoders["team1"], df["Отбор 1"])
    enc_team2 = extend_encoder(encoders["team2"], df["Отбор 2"])
    enc_league = extend_encoder(encoders["league"], df["Лига"])

    df["Отбор 1"] = enc_team1.transform(df["Отбор 1"])
    df["Отбор 2"] = enc_team2.transform(df["Отбор 2"])
    df["Лига"] = enc_league.transform(df["Лига"])

    X = df[["Отбор 1", "Отбор 2", "Лига", "Коеф"]]
    preds = model.predict_proba(X)[:, 1]  # вероятност за ValueBet == 1

    results = matches_df.copy()
    results["value"] = preds
    return results[results["value"] > 0.5].sort_values(by="value", ascending=False)
