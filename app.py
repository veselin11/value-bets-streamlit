import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Стойностни залози", layout="wide")

# Сесийна инициализация
if "history" not in st.session_state:
    st.session_state["history"] = []

if "balance" not in st.session_state:
    st.session_state["balance"] = 500

# Примерни стойностни мачове
value_bets = [
    {"Мач": "Arsenal vs Chelsea", "Пазар": "1", "Коефициент": 2.2, "Value %": 6.5, "Начален час": "21:00"},
    {"Мач": "Real Madrid vs Barcelona", "Пазар": "ГГ", "Коефициент": 1.9, "Value %": 8.1, "Начален час": "22:00"},
    {"Мач": "Bayern vs Dortmund", "Пазар": "Над 2.5", "Коефициент": 2.05, "Value %": 7.2, "Начален час": "19:30"},
]

tabs = st.tabs(["Прогнози", "История", "Настройки"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Симулирани данни")
    st.caption("Кликни на Сума за залог, за да запишеш мача в историята")

    df = pd.DataFrame(value_bets)

    for i, row in df.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1.5, 1.2, 1.2, 1.2, 2])
            col1.markdown(f"**{row['Мач']}**")
            col2.write(row["Пазар"])
            col3.write(f"{row['Коефициент']:.2f}")
            col4.write(f"{row['Value %']}%")
            col5.write(row["Начален час"])

            suggested_bet = round(st.session_state["balance"] * 0.05, -1)
            if col6.button(f"Залог {suggested_bet} лв", key=f"bet_{i}"):
                st.session_state["history"].append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Сума": suggested_bet,
                    "Печалба": 0.0,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success(f"Заложено {suggested_bet} лв на {row['Мач']} – {row['Пазар']}")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залозите")

    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])
        for i, row in history_df.iterrows():
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.5, 1.2, 1.2, 2, 2, 3])
                col1.markdown(f"**{row['Мач']}**")
                col2.write(row["Пазар"])
                col3.write(f"{row['Коефициент']:.2f}")
                col4.write(f"{row['Сума']} лв")
                col5.write(row["Дата"])
                col6.write(f"{row['Статус']}")

                if row["Статус"] == "Предстои":
                    if col7.button("Познат", key=f"win_{i}"):
                        st.session_state["history"][i]["Статус"] = "Познат"
                        st.session_state["history"][i]["Печалба"] = round((row["Коефициент"] - 1) * row["Сума"], 2)
                        st.session_state["balance"] += st.session_state["history"][i]["Печалба"]
                        st.rerun()
                    if col7.button("Грешен", key=f"lose_{i}"):
                        st.session_state["history"][i]["Статус"] = "Грешен"
                        st.session_state["history"][i]["Печалба"] = -row["Сума"]
                        st.session_state["balance"] += st.session_state["history"][i]["Печалба"]
                        st.rerun()

        total_bets = len(st.session_state["history"])
        total_staked = sum(b["Сума"] for b in st.session_state["history"])
        total_profit = sum(b["Печалба"] for b in st.session_state["history"])
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Общо залози", total_bets)
        col2.metric("Нетна печалба", f"{total_profit:.2f} лв")
        col3.metric("ROI", f"{roi:.2f}%")
        col4.metric("Текуща банка", f"{st.session_state['balance']:.2f} лв")

        # --- Графика на печалбата във времето ---
        df_profit = pd.DataFrame(st.session_state["history"])
        df_profit["Баланс"] = 500 + df_profit["Печалба"].cumsum()
        df_profit["Дата"] = pd.to_datetime(df_profit["Дата"])
        df_profit = df_profit.sort_values("Дата")

        st.subheader("Графика на растежа на банката")
        fig, ax = plt.subplots()
        ax.plot(df_profit["Дата"], df_profit["Баланс"], marker='o')
        ax.set_xlabel("Дата")
        ax.set_ylabel("Баланс (лв)")
        ax.grid(True)
        st.pyplot(fig)

        # --- Експорт на Excel ---
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="История")
            return output.getvalue()

        excel_data = to_excel(history_df)
        st.download_button(
            label="Свали като Excel файл",
            data=excel_data,
            file_name="istoria_zalozi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Няма още заложени мачове.")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки на системата")
    new_balance = st.number_input("Начална банка", min_value=100, value=int(st.session_state["balance"]), step=10)
    if st.button("Запази"):
        st.session_state["balance"] = new_balance
        st.success("Новата банка е запазена.")
        
