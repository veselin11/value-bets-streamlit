import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib

# Зареди данни
data = pd.read_csv("historical_matches.csv")

# Дефинирай фийчъри и таргет
X = data[["home_win_rate", "away_win_rate", "h2h_home_wins"]]
y = data["result"]

# Нормализирай данните
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Раздели данните
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

# Обучи модела
model = LogisticRegression()
model.fit(X_train, y_train)

# Оцени модела
y_pred = model.predict(X_test)
print(f"Точност: {accuracy_score(y_test, y_pred)*100:.2f}%")

# Запази модела и скалера
joblib.dump(model, "model.pkl")
joblib.dump(scaler, "scaler.pkl")
