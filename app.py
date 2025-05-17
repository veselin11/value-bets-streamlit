import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Функция за зареждане на данни (пример с CSV)
@st.cache_data
def load_data(path="value_bets_data.csv"):
    df = pd.read_csv(path)
    return df

# Функция за подготовка на данните и обучение на модел
def train_model(df):
    # Тук трябва да избереш кои колони ще са признаци и кое е таргета
    # Например:
    X = df.drop(columns=['target'])  # замени 'target' с името на колоната за цел
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    # Запазваме модела локално (ако искаш)
    joblib.dump(model, 'value_bet_model.pkl')

    return model, acc

# Streamlit UI
st.title("Value Bets - Обучение на Модел")

# Зареждаме данните
df = load_data()

st.write("Данни за обучение:")
st.dataframe(df.head())

# Бутон за обучение
if st.button("Обучи модел"):
    with st.spinner("Обучение в процес..."):
        model, accuracy = train_model(df)
    st.success(f"Обучението приключи! Точност на модела: {accuracy:.2%}")
    # Запазваме модела в сесията
    st.session_state['model'] = model
