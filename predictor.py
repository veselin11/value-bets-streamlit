import joblib

def load_model():
    return joblib.load("value_bet_model.pkl")

def predict_value_bet(model, matches_df):
    # Тук трябва да подготвиш features за модела
    # За пример връщаме фиктивни стойности
    import numpy as np
    # примерно, ако matches_df има N реда
    return [0.6 for _ in range(len(matches_df))]
