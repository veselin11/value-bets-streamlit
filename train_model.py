import pandas as pd
import random
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Стъпка 1: Генерираме симулирани данни
leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']
markets = ['1X2', 'Over/Under 2.5', 'Both Teams to Score']
picks = ['1', 'X', '2', 'Over 2.5', 'Under 2.5', 'Yes', 'No']

data = []
for _ in range(1000):
    league = random.choice(leagues)
    market = random.choice(markets)
    pick = random.choice(picks)
    odds = round(random.uniform(1.5, 3.5), 2)
    value = round(random.uniform(1.0, 20.0), 2)
    shots = random.randint(-10, 10)         # Преимущество в удари
    possession = random.randint(-50, 50)    # Преимущество във владеене на топката
    outcome = int(random.random() < 0.5)    # 1 = успешен залог, 0 = неуспешен

    data.append([league, market, pick, odds, value, shots, possession, outcome])

df = pd.DataFrame(data, columns=[
    'Лига', 'Пазар', 'Залог', 'Odds', 'Value %', 'Удари', 'Притежание', 'Успех'
])

# Стъпка 2: Енкодиране на категориални колони
label_encoders = {}
for col in ['Лига', 'Пазар', 'Залог']:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

# Стъпка 3: Обучение на модел
X = df.drop(columns='Успех')
y = df['Успех']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Стъпка 4: Запазване на модела и енкодерите във файлове
joblib.dump(model, 'value_bet_model.pkl')
joblib.dump(label_encoders, 'label_encoders.pkl')
print("Файловете са запазени успешно.")
