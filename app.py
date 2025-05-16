import streamlit as st
from datetime import datetime
import pandas as pd
import io
import matplotlib.pyplot as plt

# Конфигурация на страницата
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

tabs = st.tabs(["Прогнози", "История", "Графики", "Настройки"])

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

        edited_df = st.data_editor(
            history_df,
            column_config={
                "Статус": st.column_config.SelectboxColumn(
                    "Статус", help="Избери изход на мача",
                    options=["Предстои", "Печели", "Губи"]
                )
            },
            num_rows="dynamic",
            use_container_width=True
        )
        st.session_state["history"] = edited_df.to_dict("records")

        # Статистика
        resolved_bets = [b for b in st.session_state["history"] if b["Статус"] in ["Печели", "Губи"]]
        total_bets = len(st.session_state["history"])
        total_staked = sum(b["Сума"] for b in st.session_state["history"])
        total_profit = sum(b["Печалба"] if b["Статус"] == "Печели" else 0 for b in resolved_bets)
        total_loss = sum(b["Сума"] for b in resolved_bets if b["Статус"] == "Губи")
        net_profit = total_profit - total_loss
        roi = (net_profit / total_staked) * 100 if total_staked > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Залози", total_bets)
        col2.metric("Нетна печалба", f"{net_profit:.2f} лв")
        col3.metric("ROI", f"{roi:.2f}%")

        # Експорт
        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="История")
            return output.getvalue()

        st.download_button("Свали Excel файл", data=to_excel(pd.DataFrame(st.session_state["history"])), file_name="istoriya_zalozi.xlsx")
    else:
        st.info("Няма още заложени мачове.")

# === ТАБ 3: Графики ===
with tabs[2]:
    st.header("Графика на печалбата")
    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])
        df = df[df["Статус"] != "Предстои"]
        df["Нетна печалба"] = df.apply(lambda x: x["Печалба"] if x["Статус"] == "Печели" else -x["Сума"], axis=1)
        df["Натрупана печалба"] = df["Нетна печалба"].cumsum()
        df["Дата"] = pd.to_datetime(df["Дата"])

        fig, ax = plt.subplots()
        ax.plot(df["Дата"], df["Натрупана печалба"], marker="o", linestyle="-", color="green")
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
    if st.button("Запази"):
        st.session_state["balance"] = new_balance
        st.success("Новата банка е запазена!")
        st.rerun()
      
