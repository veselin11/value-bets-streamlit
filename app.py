import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Value Bets", layout="wide")

# Настройки на банката и залога
st.sidebar.header("Настройки на банката")
initial_bank = st.sidebar.number_input("Начална банка", min_value=0.0, value=500.0, step=10.0)
goal_profit = st.sidebar.number_input("Целева печалба (в %)", min_value=1, max_value=100, value=30)
goal_days = st.sidebar.number_input("Срок (в дни)", min_value=1, max_value=30, value=5)

daily_goal_profit = (goal_profit / 100) / goal_days
current_bank = initial_bank

# История на залозите (запазена в сесията)
if "history" not in st.session_state:
    st.session_state.history = []

st.title("Value Bets Приложение")

# Dummy value прогнози (пример)
value_bets = [
    {"Мач": "Team A vs Team B", "Пазар": "1X2", "Залог": "1", "Коеф": 2.20, "Вероятност": 0.55},
    {"Мач": "Team C vs Team D", "Пазар": "Над/Под", "Залог": "Над 2.5", "Коеф": 1.95, "Вероятност": 0.54},
    {"Мач": "Team E vs Team F", "Пазар": "1X2", "Залог": "2", "Коеф": 3.10, "Вероятност": 0.36}
]

# Преобразуване в DataFrame и изчисление на value %
df = pd.DataFrame(value_bets)
df["Value %"] = round((df["Коеф"] * df["Вероятност"] - 1) * 100, 2)

st.subheader("Предложения за стойностни залози")
st.dataframe(df, use_container_width=True)

# Избор и добавяне към историята
st.markdown("### Добави залог към историята")

selected_index = st.selectbox("Избери залог", df.index, format_func=lambda i: f"{df.loc[i, 'Мач']} – {df.loc[i, 'Залог']}")
stake_percent = st.slider("Процент от банката за залог", 1, 10, 2)
selected_bet = df.loc[selected_index]

stake_amount = round(current_bank * stake_percent / 100, 2)

if st.button("Добави залог"):
    st.session_state.history.append({
        "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Мач": selected_bet["Мач"],
        "Пазар": selected_bet["Пазар"],
        "Залог": selected_bet["Залог"],
        "Коеф": selected_bet["Коеф"],
        "Value %": selected_bet["Value %"],
        "Сума": stake_amount,
        "Статус": "Отворен",
        "Печалба": None
    })
    st.success("Залогът е добавен успешно!")

# История и резултати
st.markdown("### История на залозите")

history_df = pd.DataFrame(st.session_state.history)

if not history_df.empty:
    edited_df = st.data_editor(history_df, num_rows="dynamic", use_container_width=True, key="editor")

    # Изчисли нетна печалба
    def calculate_profit(row):
        if row["Статус"] == "Печели":
            return round(row["Сума"] * (row["Коеф"] - 1), 2)
        elif row["Статус"] == "Губи":
            return -row["Сума"]
        else:
            return None

    edited_df["Печалба"] = edited_df.apply(calculate_profit, axis=1)

    # Обновяване на историята
    st.session_state.history = edited_df.to_dict(orient="records")

    # Обща статистика
    total_bets = len(edited_df)
    won = (edited_df["Статус"] == "Печели").sum()
    lost = (edited_df["Статус"] == "Губи").sum()
    pending = (edited_df["Статус"] == "Отворен").sum()
    profit = edited_df["Печалба"].dropna().sum()
    roi = round(100 * profit / edited_df["Сума"].sum(), 2) if edited_df["Сума"].sum() > 0 else 0

    st.markdown(f"""
    **Общо залози:** {total_bets}  
    **Печеливши:** {won}  
    **Губещи:** {lost}  
    **Активни:** {pending}  
    **Нетна печалба:** {profit:.2f} лв  
    **ROI:** {roi:.2f} %
    """)

    # Експорт в Excel
    def to_excel(df):
        output = io.BytesIO()
        df.to_excel(output, index=False)
        return output.getvalue()

    excel_data = to_excel(edited_df)
    st.download_button("Изтегли историята като Excel", data=excel_data, file_name="value_bets_history.xlsx")

else:
    st.info("Все още няма добавени залози.")
