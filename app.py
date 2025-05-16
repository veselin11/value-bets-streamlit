import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Стойностни залози", layout="wide")

# === Сесийна инициализация ===
if "history" not in st.session_state:
    st.session_state["history"] = []

if "balance" not in st.session_state:
    st.session_state["balance"] = 500

if "bet_method" not in st.session_state:
    st.session_state["bet_method"] = "percent"

if "bet_value" not in st.session_state:
    st.session_state["bet_value"] = 5  # 5% по подразбиране

# === Примерни стойностни мачове ===
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

            # Изчисляване на сумата за залог
            if st.session_state["bet_method"] == "percent":
                suggested_bet = round(st.session_state["balance"] * st.session_state["bet_value"] / 100, -1)
            else:
                suggested_bet = st.session_state["bet_value"]

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
        st.dataframe(history_df, use_container_width=True)

        total_bets = len(history_df)
        total_staked = sum(b["Сума"] for b in st.session_state["history"])
        total_profit = sum(b["Печалба"] for b in st.session_state["history"])
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Залози", total_bets)
        col2.metric("Нетна печалба", f"{total_profit:.2f} лв")
        col3.metric("ROI", f"{roi:.2f}%")
    else:
        st.info("Няма още заложени мачове.")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки на системата")

    new_balance = st.number_input("Начална банка", min_value=100, value=st.session_state["balance"], step=10)
    st.subheader("Метод за изчисляване на залога")

    method = st.selectbox("Избери метод", ["Процент от банката", "Фиксирана сума"], 
                          index=0 if st.session_state["bet_method"] == "percent" else 1)

    if method == "Процент от банката":
        percent = st.slider("Процент от банката", min_value=1, max_value=20, value=st.session_state.get("bet_value", 5), step=1)
        bet_method = "percent"
        bet_value = percent
    else:
        fixed = st.number_input("Фиксирана сума (лв)", min_value=10, max_value=1000, value=st.session_state.get("bet_value", 50), step=10)
        bet_method = "fixed"
        bet_value = fixed

    if st.button("Запази"):
        st.session_state["balance"] = new_balance
        st.session_state["bet_method"] = bet_method
        st.session_state["bet_value"] = bet_value
        st.success("Настройките са запазени успешно.")
