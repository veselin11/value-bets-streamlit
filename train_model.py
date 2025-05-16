# train_model.py

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# Зареждане на данни
df = pd.read_csv("matches.csv")

# Филтриране на необходими колони
df = df[['league', 'team1', 'team2', 'market', 'pick', 'odds', 'result']]

# Премахване на редове с липсващи стойности
df = df.dropna()

# Енкодиране на категорийни стойности
le = LabelEncoder()
for col in ['league', 'team1', 'team2', 'market', 'pick']:
    df[col] = le.fit_transform(df[col].astype(str))

# Целева променлива: 1 ако залогът е спечелен, 0 иначе
df['target'] = df['result'].apply(lambda x: 1 if x == 'win' else 0)

# Функции и цел
X = df[['league', 'team1', 'team2', 'market', 'pick', 'odds']]
y = df['target']

# Разделяне на обучаващи и тестови данни
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Създаване и обучение на модела
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Запазване на модела и енкодера
joblib.dump(model, 'value_bet_model.pkl')
joblib.dump(le, 'label_encoder.pkl')

print("✅ Обучението завърши и моделите са запазени.")
