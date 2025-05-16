import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Value Bets Tracker", layout="wide")

# Заглавие
st.title("История на залозите")

# Dummy база за история (в реалното приложение се зарежда от база или файл)
if "history" not in st.session_state:
    st.session_state.history = []

# Форма за добавяне на нов запис
with st.expander("Добави нов залог"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Дата", datetime.date.today())
        bet_type = st.selectbox("Тип залог", ["1", "X", "2", "Over", "Under", "Asian Handicap"])
        stake = st.number_input("Залог (лв)", min_value=1.0, step=1.0)
    with col2:
        match = st.text_input("Мач")
        odds = st.number_input("Коефициент", min_value=1.01, step=0.01)
        result = st.selectbox("Резултат", ["Чака се", "Спечелен", "Загубен"])

    if st.button("Добави залог"):
        st.session_state.history.append({
            "Дата": date.strftime("%Y-%m-%d"),
            "Мач": match,
            "Тип": bet_type,
            "Коефициент": odds,
            "Залог": stake,
            "Резултат": result
        })
        st.success("Залогът е добавен успешно.")

# Преобразуване в DataFrame
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)

    # Изчисляване на печалба
    def calc_profit(row):
        if row["Резултат"] == "Спечелен":
            return round(row["Залог"] * (row["Коефициент"] - 1), 2)
        elif row["Резултат"] == "Загубен":
            return -row["Залог"]
        return 0.0

    df["Печалба (лв)"] = df.apply(calc_profit, axis=1)

    # Обща статистика
    total_bets = len(df)
    won_bets = df[df["Резултат"] == "Спечелен"].shape[0]
    lost_bets = df[df["Резултат"] == "Загубен"].shape[0]
    waiting = df[df["Резултат"] == "Чака се"].shape[0]
    total_profit = df["Печалба (лв)"].sum()
    roi = (total_profit / df["Залог"].sum()) * 100 if df["Залог"].sum() > 0 else 0

    st.subheader("Статистика")
    st.markdown(f"**Общо залози:** {total_bets}")
    st.markdown(f"**Спечелени:** {won_bets} | Загубени: {lost_bets} | Чака се: {waiting}")
    st.markdown(f"**Обща печалба:** {total_profit:.2f} лв")
    st.markdown(f"**ROI:** {roi:.2f}%")

    st.subheader("История")
    st.dataframe(df, use_container_width=True)

else:
    st.info("Няма въведени залози все още.")
    
