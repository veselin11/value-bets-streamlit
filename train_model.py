import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

def train():
    data = pd.read_csv("football_data.csv")
    X = data.drop("target", axis=1)
    y = data["target"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, "value_bet_model.pkl")

if __name__ == "__main__":
    train()
