import joblib
import numpy as np

def predict(matches_df):
    model = joblib.load("value_bet_model.pkl")
    encoders = joblib.load("label_encoders.pkl")

    df = matches_df.copy()

    def extend_encoder(encoder, values):
        known = set(encoder.classes_)
        unknown = set(values) - known
        if unknown:
            encoder.classes_ = np.array(list(encoder.classes_) + list(unknown))
        return encoder

    enc_team1 = extend_encoder(encoders["team1"], df["Отбор 1"])
    enc_team2 = extend_encoder(encoders["team2"], df["Отбор 2"])
    enc_league = extend_encoder(encoders["league"], df["Лига"])

    df["Отбор 1"] = enc_team1.transform(df["Отбор 1"])
    df["Отбор 2"] = enc_team2.transform(df["Отбор 2"])
    df["Лига"] = enc_league.transform(df["Лига"])

    X = df[["Отбор 1", "Отбор 2", "Лига", "Коеф"]]

    preds_proba = model.predict_proba(X)[:, 1]

    value = preds_proba * df["Коеф"] - 1

    df["value"] = value

    return df[df["value"] > 0].sort_values(by="value", ascending=False)
