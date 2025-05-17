import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

def train():
    data = pd.read_csv("football_data.csv")

    # Създаваме енкодери за категориални колони
    le_team1 = LabelEncoder()
    le_team2 = LabelEncoder()
    le_league = LabelEncoder()

    data["Отбор 1"] = le_team1.fit_transform(data["Отбор 1"])
    data["Отбор 2"] = le_team2.fit_transform(data["Отбор 2"])
    data["Лига"] = le_league.fit_transform(data["Лига"])

    X = data.drop("target", axis=1)
    y = data["target"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Запазваме модела
    joblib.dump(model, "value_bet_model.pkl")

    # Запазваме енкодерите
    encoders = {
        "team1": le_team1,
        "team2": le_team2,
        "league": le_league
    }
    joblib.dump(encoders, "label_encoders.pkl")

if __name__ == "__main__":
    train()
