import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

def load_and_prepare(csv_files):
    dfs = []
    for file in csv_files:
        df = pd.read_csv(file)
        # Избиране само на важни колони, според примера
        cols = ['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A', 'FTR']
        # Проверяваме дали всички колони съществуват в дадения файл
        if all(col in df.columns for col in cols):
            dfs.append(df[cols].dropna())
        else:
            print(f"Warning: Някои колони липсват във файла {file}. Пропуснат.")
    if not dfs:
        raise ValueError("Няма валидни файлове с нужните колони.")
    data = pd.concat(dfs, ignore_index=True)
    return data

def prepare_features(data):
    le = LabelEncoder()
    data['FTR_encoded'] = le.fit_transform(data['FTR'])
    X = data[['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A']]
    y = data['FTR_encoded']
    return X, y, le

def train_and_save_model(csv_files):
    data = load_and_prepare(csv_files)
    X, y, le = prepare_features(data)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # Запазваме модела и LabelEncoder-а за после
    joblib.dump(model, 'value_bet_model.pkl')
    joblib.dump(le, 'label_encoder.pkl')
    print("Моделът и LabelEncoder-а са запазени успешно!")

if __name__ == "__main__":
    # Тук добави пътищата към твоите CSV файлове
    csv_files = [
        'E0.csv',
        'SP1.csv',
        # 'path/to/other_files.csv',
    ]
    train_and_save_model(csv_files)
