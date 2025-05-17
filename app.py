import streamlit as st
import time

def train_model():
    time.sleep(2)  # симулация на обучение
    return 0.9

st.title("Value Bets - Обучение на модел")

if st.button("Обучи модел"):
    with st.spinner("Обучение в процес..."):
        accuracy = train_model()
    st.success(f"Обучението приключи. Точност: {accuracy:.2f}")

