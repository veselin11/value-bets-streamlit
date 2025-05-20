import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

# ======== 1. Зареждане на CSV файла с мачове ========
df = pd.read_csv("epl_matches.csv")  # замени с името на твоя файл

# ======== 2. Изчисляване на статистики за отборите ========
df["home_win"] = df["home_goals"] > df["away_goals"]
df["draw"] = df["home_goals"] == df["away_goals"]

df["result"] = np.select(
    [df["home_win"], df["draw"]],
    [0, 1],
    default=2  # 0=Home win, 1=Draw, 2=Away win
)

# Изчисляване на статистики
df["home_avg_goals"] = df["home_goals"].rolling(window=5).mean().fillna(1.2)
df["away_avg_goals"] = df["away_goals"].rolling(window=5).mean().fillna(1.0)
df["home_win_rate"] = df["home_win"].rolling(window=5).mean().fillna(0.5)
df["away_win_rate"] = (~df["home_win"]).rolling(window=5).mean().fillna(0.3)

# ======== 3. Подготовка на входове и изходи ========
features = df[["home_avg_goals", "away_avg_goals", "home_win_rate", "away_win_rate"]]
labels = df["result"]

X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

# ======== 4. Машинно обучение ========
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

model = LogisticRegression(multi_class='multinomial', max_iter=1000)
model.fit(X_train_scaled, y_train)

# ======== 5. Запазване на модела ========
joblib.dump(model, "model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Моделът е обучен и запазен успешно.")
