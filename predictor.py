import joblib

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

def predict(df):
    model, encoders = load_model()
    X = prepare_features(df, encoders)
    preds = model.predict_proba(X)[:, 1]  # вероятност за клас 1 (value bet)
    return preds
