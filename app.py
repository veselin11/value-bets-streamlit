import streamlit as st
from datetime import datetime
import pandas as pd

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

            suggested_bet = round(st.session_state["balance"] * 0.05, -1)  # 5% от банката, закръглено
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
        for i, bet in enumerate(st.session_state["history"]):
            with st.container(border=True):
                cols = st.columns([3, 1, 1.2, 1.2, 1.5, 2, 1.2])
                cols[0].markdown(f"**{bet['Мач']}**")
                cols[1].write(bet["Пазар"])
                cols[2].write(f"{bet['Коефициент']:.2f}")
                cols[3].write(f"{bet['Сума']} лв")
                cols[4].write(f"{bet['Печалба']} лв")
                cols[5].write(bet["Дата"])
                if cols[6].button("Изтрий", key=f"delete_{i}"):
                    st.session_state["history"].pop(i)
                    st.experimental_rerun()

        history_df = pd.DataFrame(st.session_state["history"])
        if not history_df.empty:
            total_bets = len(history_df)
            total_staked = history_df["Сума"].sum()
            total_profit = history_df["Печалба"].sum()
            roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Залози", total_bets)
            col2.metric("Нетна печалба", f"{total_profit:.2f} лв")
            col3.metric("ROI", f"{roi:.2f}%")

            # Експорт в CSV
            csv = history_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Експортирай историята (CSV)",
                data=csv,
                file_name="istoriya_zalozi.csv",
                mime="text/csv"
            )
    else:
        st.info("Няма още заложени мачове.")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки на системата")
    new_balance = st.number_input("Начална банка", min_value=100, value=st.session_state["balance"], step=10)
    if st.button("Запази"):
        st.session_state["balance"] = new_balance
        st.success("Новата банка е запазена.")
