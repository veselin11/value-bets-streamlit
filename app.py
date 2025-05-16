import streamlit as st
from datetime import datetime
import pandas as pd
import io
import matplotlib.pyplot as plt

# --- Конфигурация ---
st.set_page_config(page_title="Стойностни залози", layout="wide")

# --- Сесия ---
if "history" not in st.session_state:
    st.session_state["history"] = []

if "balance" not in st.session_state:
    st.session_state["balance"] = 500

if "stake_percent" not in st.session_state:
    st.session_state["stake_percent"] = 5  # % от банката

# --- Примерни мачове ---
value_bets = [
    {"Мач": "Arsenal vs Chelsea", "Пазар": "1", "Коефициент": 2.2, "Value %": 6.5, "Начален час": "21:00"},
    {"Мач": "Real Madrid vs Barcelona", "Пазар": "ГГ", "Коефициент": 1.9, "Value %": 8.1, "Начален час": "22:00"},
    {"Мач": "Bayern vs Dortmund", "Пазар": "Над 2.5", "Коефициент": 2.05, "Value %": 7.2, "Начален час": "19:30"},
]

tabs = st.tabs(["Прогнози", "История", "Графики", "Настройки"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Симулирани данни")
    df = pd.DataFrame(value_bets)

    for i, row in df.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1.5, 1.2, 1.2, 1.2, 2])
            col1.markdown(f"**{row['Мач']}**")
            col2.write(row["Пазар"])
            col3.write(f"{row['Коефициент']:.2f}")
            col4.write(f"{row['Value %']}%")
            col5.write(row["Начален час"])

            suggested_bet = round(st.session_state["balance"] * st.session_state["stake_percent"] / 100, -1)
            if col6.button(f"Залог {suggested_bet} лв", key=f"bet_{i}"):
                profit = round((row["Коефициент"] - 1) * suggested_bet, 2)
                st.session_state["history"].append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Сума": suggested_bet,
                    "Печалба": profit,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success(f"Заложено {suggested_bet} лв на {row['Мач']} – {row['Пазар']}")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залозите")
    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])

        # Добавяне на падащи менюта за резултат
        for i in range(len(history_df)):
            if history_df.at[i, "Статус"] == "Предстои":
                result = st.selectbox(
                    f"Резултат: {history_df.at[i, 'Мач']} ({history_df.at[i, 'Пазар']})",
                    options=["-", "Печели", "Губи"],
                    key=f"result_{i}"
                )
                if result == "Печели":
                    history_df.at[i, "Статус"] = "Печели"
                    history_df.at[i, "Печалба"] = round((history_df.at[i, "Коефициент"] - 1) * history_df.at[i, "Сума"], 2)
                elif result == "Губи":
                    history_df.at[i, "Статус"] = "Губи"
                    history_df.at[i, "Печалба"] = -history_df.at[i, "Сума"]

        # Запазване на актуализирана история
        st.session_state["history"] = history_df.to_dict("records")

        st.dataframe(history_df, use_container_width=True)

        total_bets = len(history_df)
        total_staked = sum(b["Сума"] for b in st.session_state["history"])
        total_profit = sum(b["Печалба"] for b in st.session_state["history"])
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Залози", total_bets)
        col2.metric("Нетна печалба", f"{total_profit:.2f} лв")
        col3.metric("ROI", f"{roi:.2f}%")

        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="История")
            return output.getvalue()

        excel_data = to_excel(history_df)
        st.download_button("Свали Excel файл", data=excel_data, file_name="istoriya_zalozi.xlsx")
    else:
        st.info("Няма още заложени мачове.")

# === ТАБ 3: Графики ===
with tabs[2]:
    st.header("Графика на печалбата")
    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])
        history_df["Дата"] = pd.to_datetime(history_df["Дата"])
        history_df = history_df.sort_values("Дата")
        history_df["Натрупана печалба"] = history_df["Печалба"].cumsum()

        fig, ax = plt.subplots()
        ax.plot(history_df["Дата"], history_df["Натрупана печалба"], marker="o", linestyle="-",
                color="green" if history_df["Натрупана печалба"].iloc[-1] >= 0 else "red")
        ax.set_title("Натрупана печалба във времето")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Печалба (лв)")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Няма данни за показване.")

# === ТАБ 4: Настройки ===
with tabs[3]:
    st.header("Настройки на системата")

    new_balance = st.number_input("Начална банка", min_value=100, value=st.session_state["balance"], step=10)
    stake_percent = st.slider("Процент от банката за залог", min_value=1, max_value=20, value=st.session_state["stake_percent"], step=1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Запази"):
            st.session_state["balance"] = new_balance
            st.session_state["stake_percent"] = stake_percent
            st.success("Настройките са запазени.")
            st.rerun()

    with col2:
        if st.button("Изчисти историята"):
            st.session_state["history"] = []
            st.success("Историята е изчистена!")
            st.rerun()
