import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# === Сесия ===
if "history" not in st.session_state:
    st.session_state["history"] = []
if "balance" not in st.session_state:
    st.session_state["balance"] = 500.0

# === Примерни прогнози ===
value_bets = [
    {"Мач": "Барселона - Реал", "Пазар": "1Х", "Коефициент": 2.10, "Value %": 15, "Час": "22:00"},
    {"Мач": "Арсенал - Челси", "Пазар": "Над 2.5", "Коефициент": 1.85, "Value %": 12, "Час": "21:30"},
    {"Мач": "Байерн - Борусия", "Пазар": "Х2", "Коефициент": 3.25, "Value %": 18, "Час": "19:45"},
]

# === Цветове по value ===
def get_color(value):
    if value >= 20:
        return "#d3f9d8"
    elif value >= 15:
        return "#fff3bf"
    return "#ffc9c9"

# === Tabs ===
tabs = st.tabs(["Прогнози", "История", "Статистика"])

# === TAB 1 ===
with tabs[0]:
    st.markdown("## Днешни стойностни залози")

    for i, row in enumerate(value_bets):
        bg = get_color(row["Value %"])
        with st.container():
            st.markdown(f"""
            <div style="background-color:{bg}; padding:1rem; border-radius:12px; margin-bottom:10px;">
                <div style="font-size:18px; font-weight:bold;">{row['Мач']}</div>
                <div style="color:#555;">Пазар: {row['Пазар']} | Коеф.: {row['Коефициент']} | Value: {row['Value %']}% | Час: {row['Час']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Залагай ({round(st.session_state['balance']*0.05, -1)} лв)", key=f"bet{i}"):
                amount = round(st.session_state["balance"] * 0.05, -1)
                profit = round((row["Коефициент"] - 1) * amount, 2)
                st.session_state["history"].append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Сума": amount,
                    "Печалба": profit,
                    "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Статус": "Предстои"
                })
                st.success("Залогът е добавен.")
                st.rerun()

# === TAB 2 ===
with tabs[1]:
    st.markdown("## История на залозите")

    if not st.session_state["history"]:
        st.info("Няма направени залози.")
    else:
        for i, row in enumerate(st.session_state["history"]):
            color = {"Печели": "green", "Губи": "red", "Предстои": "gray"}.get(row["Статус"], "gray")
            with st.container():
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:0.8rem; border-radius:10px; margin-bottom:10px;">
                    <b>{row['Мач']}</b><br>
                    Пазар: {row['Пазар']} | Коеф.: {row['Коефициент']}<br>
                    Сума: {row['Сума']} лв | Печалба: {row['Печалба']} лв<br>
                    <span style='color:{color}; font-weight:bold'>Статус: {row['Статус']}</span> | {row['Дата']}
                </div>
                """, unsafe_allow_html=True)

                new_status = st.selectbox("Промени статус", ["Предстои", "Печели", "Губи"], key=f"status_{i}", index=["Предстои", "Печели", "Губи"].index(row["Статус"]))
                if new_status != row["Статус"]:
                    st.session_state["history"][i]["Статус"] = new_status
                    st.rerun()

# === TAB 3 ===
with tabs[2]:
    st.markdown("## Статистика")

    df = pd.DataFrame(st.session_state["history"])
    if df.empty:
        st.warning("Все още няма статистика.")
    else:
        total = len(df)
        won = df[df["Статус"] == "Печели"]
        lost = df[df["Статус"] == "Губи"]

        net = won["Печалба"].sum() - lost["Сума"].sum()
        roi = net / df["Сума"].sum() * 100 if df["Сума"].sum() else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Залози", total)
        col2.metric("Нетна печалба", f"{net:.2f} лв")
        col3.metric("ROI", f"{roi:.2f} %")

        df["Дата"] = pd.to_datetime(df["Дата"])
        df = df.sort_values("Дата")
        st.line_chart(df.groupby("Дата")["Печалба"].sum().cumsum())
