import pandas as pd
import joblib
import numpy as np

def predict(matches_df):
    model = joblib.load("value_bet_model.pkl")
    encoders = joblib.load("label_encoders.pkl")

    df = matches_df.copy()

    def encode_with_unseen(encoder, values):
        classes = set(encoder.classes_)
        encoded = []
        for v in values:
            if v in classes:
                encoded.append(encoder.transform([v])[0])
            else:
                # unseen label -> encode as -1
                encoded.append(-1)
        return np.array(encoded)

    df["Отбор 1"] = encode_with_unseen(encoders["team1"], df["Отбор 1"])
    df["Отбор 2"] = encode_with_unseen(encoders["team2"], df["Отбор 2"])
    df["Лига"] = encode_with_unseen(encoders["league"], df["Лига"])

    X = df[["Отбор 1", "Отбор 2", "Лига", "Коеф"]]

    # Заменяме -1 с 0 (най-често срещана категория)
    X = X.replace(-1, 0)

    preds = model.predict_proba(X)[:, 1]

    results = matches_df.copy()
    results["value"] = preds

    return results[results["value"] > 0.5].sort_values(by="value", ascending=False)
