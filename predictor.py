import pickle
import pandas as pd

def load_model(path="value_bet_model.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

def load_encoders(path="label_encoders.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

def preprocess_data(df, encoders):
    df_copy = df.copy()
    for col in encoders:
        if col in df_copy:
            df_copy[col] = encoders[col].transform(df_copy[col])
    return df_copy

def predict_probabilities(model, df, encoders):
    X = preprocess_data(df, encoders)
    return model.predict_proba(X)
