import streamlit as st
from datetime import datetime
import pandas as pd
import io
import matplotlib.pyplot as plt
import os

# === Конфигурация на страницата ===
st.set_page_config(page_title="Стойностни залози", layout="wide")

# === Сесийна инициализация ===
if "history" not in st.session_state:
    st.session_state["history"] = []

if "balance" not in st.session_state:
    st.session_state["balance"] = 500

# === Примерни залози за днес ===
value_bets = [
    {"Мач": "Man City vs Arsenal", "Пазар": "Над 2.5", "Коефициент": 1.85, "Value %": 9.1, "Начален час": "21:00"},
    {"Мач": "Juventus vs Milan", "Пазар": "ГГ", "Коефициент": 2.05, "Value %": 7.2, "Начален час": "21:45"},
    {"Мач": "Leipzig vs Bayern", "Пазар": "2", "Коефициент": 2.30, "Value %": 5.5, "Начален час": "19:30"},
    {"Мач": "PSG vs Lyon", "Пазар": "1", "Коефициент": 1.60, "Value %": 3.8, "Начален час": "22:00"},
]

# === Сигурност според Value % ===
def get_confidence_color(value_percent):
    if value_percent >= 8:
        return "#d4edda"  # Светлозелено
    elif value_percent >= 5:
        return "#fff3cd"  # Светложълто
    else:
        return "#f8d7da"  # Светлочервено

# === Tabs ===
tabs = st.tabs(["Прогнози", "История", "Графика", "Настройки"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Днес")
    st.caption("Кликни на бутона за залог, за да го добавиш в историята.")

    df = pd.DataFrame(value_bets)

    for i, row in df.iterrows():
        bg_color = get_confidence_color(row["Value %"])
        with st.container():
            st.markdown(
                f"""<div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                    <b>{row['Мач']}</b> | Пазар: {row['Пазар']} | Коеф.: {row['Коефициент']:.2f} | Value: {row['Value %']}% | Час: {row['Начален час']}
                    <br><br>
                    <form action="" method="post">
                        <button name="bet_{i}" type="submit" style="background-color:#007bff; color:white; border:none; padding:5px 15px; border-radius:5px;">Залог {round(st.session_state['balance'] * 0.05, -1)} лв</button>
                    </form>
                </div>""",
                unsafe_allow_html=True,
            )

            if st.form_submit_button(f"bet_{i}"):
                suggested_bet = round(st.session_state["balance"] * 0.05, -1)
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
                st.experimental_rerun()

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залозите")
    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])

        # Оцветяване на редовете според статус
        def highlight_status(row):
            color = ""
            if row["Статус"] == "Печели":
                color = "#d4edda"
            elif row["Статус"] == "Губи":
                color = "#f8d7da"
            else:
                color = "#fff3cd"
            return [f"background-color: {color}"] * len(row)

        st.dataframe(
            history_df.style.apply(highlight_status, axis=1),
            use_container_width=True
        )

        # Метрики
        total_bets = len(history_df)
        total_staked = history_df["Сума"].sum()
        total_profit = history_df["Печалба"].sum()
        roi = (total_profit / total_staked) * 100 if total_staked else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Общо залози", total_bets)
        col2.metric("Нетна печалба", f"{total_profit:.2f} лв")
        col3.metric("ROI", f"{roi:.2f}%")

        # Експорт
        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="История")
            return output.getvalue()

        excel_data = to_excel(history_df)
        st.download_button("Свали Excel", data=excel_data, file_name="istoriya_zalozi.xlsx")
    else:
        st.info("Все още няма записани залози.")

# === ТАБ 3: Графика ===
with tabs[2]:
    st.header("Графика на печалбата")
    if st.session_state["history"]:
        graph_df = pd.DataFrame(st.session_state["history"])
        graph_df["Дата"] = pd.to_datetime(graph_df["Дата"])
        graph_df["Натрупана печалба"] = graph_df["Печалба"].cumsum()

        fig, ax = plt.subplots()
        ax.plot(graph_df["Дата"], graph_df["Натрупана печалба"], marker="o", color="green")
        ax.set_title("Натрупана печалба")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Печалба (лв)")
        ax.grid(True)
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Няма данни за графика.")

# === ТАБ 4: Настройки ===
with tabs[3]:
    st.header("Настройки")
    new_balance = st.number_input("Начална банка", min_value=100, value=st.session_state["balance"], step=10)
    if st.button("Запази"):
        st.session_state["balance"] = new_balance
        st.success("Банката е обновена.")
        st.rerun()
