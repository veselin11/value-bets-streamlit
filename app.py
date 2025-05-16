import streamlit as st
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
st.set_page_config(layout="wide", page_title="Value Bets Tracker")

=== Инициализация на сесия ===

if 'bets' not in st.session_state: st.session_state.bets = [] if 'bank' not in st.session_state: st.session_state.bank = 500.0

=== Цветове според сигурност ===

def get_confidence_color(value): if value >= 15: return "#d4edda"  # светло зелено elif value >= 10: return "#fff3cd"  # светло жълто else: return "#f8d7da"  # светло червено

=== Таб: Прогнози ===

if "tab" not in st.session_state: st.session_state.tab = "Прогнози"

st.sidebar.title("Меню") tab = st.sidebar.radio("Избери таб", ["Прогнози", "История", "Статистика"])

if tab == "Прогнози": st.title("Value Залози - Прогнози за днес")

sample_bets = [
    {"мач": "Ливърпул - Челси", "пазар": "1Х2", "прогноза": "1", "коеф": 2.10, "value": 14.5},
    {"мач": "Барселона - Реал Мадрид", "пазар": "Над/Под 2.5", "прогноза": "Над 2.5", "коеф": 1.95, "value": 12.0},
    {"мач": "Ювентус - Милан", "пазар": "Двоен шанс", "прогноза": "1X", "коеф": 1.70, "value": 9.8},
]

for i, bet in enumerate(sample_bets):
    with st.container():
        color = get_confidence_color(bet["value"])
        st.markdown(f"""
            <div style='background-color: {color}; padding: 10px; border-radius: 10px;'>
            <b>Мач:</b> {bet['мач']}<br>
            <b>Пазар:</b> {bet['пазар']}<br>
            <b>Прогноза:</b> {bet['прогноза']}<br>
            <b>Коефициент:</b> {bet['коеф']}<br>
            <b>Value %:</b> {bet['value']:.1f}%
            </div>
        """, unsafe_allow_html=True)

        if st.button(f"Залагай {i+1}"):
            new_bet = {
                "дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "мач": bet["мач"],
                "пазар": bet["пазар"],
                "прогноза": bet["прогноза"],
                "коеф": bet["коеф"],
                "статус": "предстои",
                "value": bet["value"]
            }
            st.session_state.bets.append(new_bet)
            st.success("Залогът е добавен в историята!")

=== Таб: История ===

elif tab == "История": st.title("История на Залозите") if st.session_state.bets: df = pd.DataFrame(st.session_state.bets)

for i in range(len(df)):
        if df.loc[i, "статус"] == "предстои":
            резултат = st.selectbox(
                f"Статус за мача: {df.loc[i, 'мач']}",
                ["предстои", "печели", "губи"],
                key=f"статус_{i}"
            )
            df.loc[i, "статус"] = резултат
            st.session_state.bets[i]["статус"] = резултат

    df["прибиране"] = df.apply(
        lambda row: round((row["коеф"] - 1) if row["статус"] == "печели" else -1, 2), axis=1
    )
    st.dataframe(df.drop(columns=["прибиране"]))
else:
    st.info("Все още няма добавени залози.")

=== Таб: Статистика ===

elif tab == "Статистика": st.title("Статистика") bets_df = pd.DataFrame(st.session_state.bets) if not bets_df.empty: total_bets = len(bets_df) won = bets_df[bets_df["статус"] == "печели"].shape[0] lost = bets_df[bets_df["статус"] == "губи"].shape[0] pending = bets_df[bets_df["статус"] == "предстои"].shape[0] roi = bets_df.apply(lambda row: (row["коеф"] - 1) if row["статус"] == "печели" else (-1 if row["статус"] == "губи" else 0), axis=1).sum()

col1, col2, col3, col4 = st.columns(4)
    col1.metric("Общо залози", total_bets)
    col2.metric("Печеливши", won)
    col3.metric("Губещи", lost)
    col4.metric("ROI", f"{roi:.2f} единици")

    chart_data = bets_df.copy()
    chart_data["резултат"] = chart_data.apply(lambda row: (row["коеф"] - 1) if row["статус"] == "печели" else (-1 if row["статус"] == "губи" else 0), axis=1)
    chart_data["кумулативно"] = chart_data["резултат"].cumsum()
    fig, ax = plt.subplots()
    ax.plot(chart_data["кумулативно"], marker='o')
    ax.set_title("Кумулативна Печалба")
    ax.set_ylabel("Печалба (единици)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    st.pyplot(fig)
else:
    st.info("Няма налични данни за статистика.")

