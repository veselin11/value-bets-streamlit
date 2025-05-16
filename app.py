import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import random

st.set_page_config(page_title="Стойностни залози", layout="wide")

# === Сесийна инициализация ===
if "history" not in st.session_state:
    st.session_state["history"] = []
if "balance" not in st.session_state:
    st.session_state["balance"] = 500.0

# === Функция за генериране на прогнози ===
def generate_value_bets():
    sample_matches = [
        ("Барселона", "Реал"), ("Арсенал", "Челси"), ("Байерн", "Борусия"),
        ("Интер", "Милан"), ("Ювентус", "Наполи"), ("Ливърпул", "Манчестър Юн"),
        ("ПСЖ", "Марсилия"), ("Аякс", "Фейенорд")
    ]
    markets = ["1", "2", "1Х", "Х2", "Над 2.5", "Под 2.5"]
    bets = []
    for _ in range(4):
        home, away = random.choice(sample_matches)
        bets.append({
            "Мач": f"{home} - {away}",
            "Пазар": random.choice(markets),
            "Коефициент": round(random.uniform(1.6, 3.5), 2),
            "Value %": random.randint(10, 25),
            "Начален час": f"{random.randint(18, 22)}:{random.choice(['00', '15', '30', '45'])}"
        })
    return bets

# === Съхраняване на прогнозите в session_state ===
if "value_bets" not in st.session_state:
    st.session_state["value_bets"] = generate_value_bets()

# === Функция за обновяване на прогнозите ===
def refresh_bets():
    st.session_state["value_bets"] = generate_value_bets()
    st.rerun()

# === Функция за цветова индикация със semi-transparent фон ===
def get_confidence_color(value_percent):
    if value_percent >= 20:
        return "rgba(178, 242, 187, 0.4)"  # зеленикав
    elif value_percent >= 15:
        return "rgba(255, 224, 102, 0.4)"  # жълтеникав
    else:
        return "rgba(255, 168, 168, 0.4)"  # червеникав

# === ТАБОВЕ ===
tabs = st.tabs(["Прогнози", "История", "Статистика"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Днес")
    st.caption("Кликни на бутона за залог, за да го добавиш в историята.")

    st.button("Обнови прогнозите", on_click=refresh_bets)

    df = pd.DataFrame(st.session_state["value_bets"])

    for i, row in df.iterrows():
        bg_color = get_confidence_color(row["Value %"])
        with st.container():
            st.markdown(
                f"""<div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                    <b>{row['Мач']}</b> | Пазар: {row['Пазар']} | Коеф.: {row['Коефициент']:.2f} | Value: {row['Value %']}% | Час: {row['Начален час']}
                </div>""",
                unsafe_allow_html=True,
            )

            col1, _ = st.columns([1, 4])
            if col1.button(f"Залог {round(st.session_state['balance'] * 0.05, -1)} лв", key=f"bet_{i}"):
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
                st.success(f"Залогът е добавен за {row['Мач']}")
                st.rerun()

# === ТАБ 2: История ===
with tabs[1]:
    st.title("История на залозите")
    hist_df = pd.DataFrame(st.session_state["history"])

    def status_color(status):
        return {
            "Печели": "rgba(212, 237, 218, 0.6)",
            "Губи": "rgba(248, 215, 218, 0.6)",
            "Предстои": "rgba(255, 243, 205, 0.6)"
        }.get(status, "white")

    if not hist_df.empty:
        for i, row in hist_df.iterrows():
            cols = st.columns([2, 2, 1, 1, 1, 1])
            bg = status_color(row["Статус"])
            with cols[0]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Мач']}</div>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Пазар']}</div>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Коефициент']}</div>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"<div style='background-color:{bg}; padding:5px; border-radius:5px'>{row['Сума']} лв</div>", unsafe_allow_html=True)
            with cols[4]:
                status = st.selectbox("", ["Предстои", "Печели", "Губи"], index=["Предстои", "Печели", "Губи"].index(row["Статус"]), key=f"status_{i}")
                st.session_state["history"][i]["Статус"] = status
    else:
        st.info("Няма още запазени залози.")

# === ТАБ 3: Статистика ===
with tabs[2]:
    st.title("Обща статистика")
    df = pd.DataFrame(st.session_state["history"])
    if not df.empty:
        total_bets = len(df)
        won = df[df["Статус"] == "Печели"]
        lost = df[df["Статус"] == "Губи"]

        net_profit = won["Печалба"].sum() - lost["Сума"].sum()
        roi = net_profit / df["Сума"].sum() * 100 if df["Сума"].sum() > 0 else 0

        st.metric("Залози", total_bets)
        st.metric("Печалба", f"{net_profit:.2f} лв")
        st.metric("ROI", f"{roi:.2f}%")

        st.line_chart(df.groupby("Дата")["Печалба"].sum().cumsum())
    else:
        st.info("Няма налични данни за статистика.")
