import streamlit as st
from datetime import datetime
import pandas as pd
import io
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Стойностни залози", layout="wide")

=== Сесийна инициализация ===

if "history" not in st.session_state: if os.path.exists("history.csv"): st.session_state["history"] = pd.read_csv("history.csv").to_dict(orient="records") else: st.session_state["history"] = []

if "balance" not in st.session_state: st.session_state["balance"] = 500

=== Примерни стойностни мачове ===

today = datetime.now().strftime("%Y-%m-%d") value_bets = [ {"Мач": "Arsenal vs Chelsea", "Пазар": "1", "Коефициент": 2.2, "Value %": 6.5, "Начален час": f"{today} 21:00", "Сигурност": 3}, {"Мач": "Real Madrid vs Barcelona", "Пазар": "ГГ", "Коефициент": 1.9, "Value %": 8.1, "Начален час": f"{today} 22:00", "Сигурност": 4}, {"Мач": "Bayern vs Dortmund", "Пазар": "Над 2.5", "Коефициент": 2.05, "Value %": 7.2, "Начален час": f"{today} 19:30", "Сигурност": 2}, {"Мач": "Milan vs Inter", "Пазар": "Точен резултат 2:1", "Коефициент": 10.0, "Value %": 12.4, "Начален час": f"{today} 20:00", "Сигурност": 1}, {"Мач": "PSG vs Lyon", "Пазар": "Двоен шанс 1X", "Коефициент": 1.5, "Value %": 4.1, "Начален час": f"{today} 21:30", "Сигурност": 5}, ]

=== Стилове ===

STYLE_MAP = { 1: "#ffcccc",  # Ниска сигурност - червеникаво 2: "#ffe0b2",  # Слаба 3: "#fff9c4",  # Средна 4: "#c8e6c9",  # Висока 5: "#a5d6a7"   # Много висока - зелено }

STATUS_COLORS = { "Познат": "#d0f0c0", "Грешен": "#f8d7da", "Предстои": "#f0f0f0", "Очаква резултат": "#e2e3e5" }

=== Tabs ===

tabs = st.tabs(["Прогнози", "История", "Графики", "Настройки"])

=== TAB 1: Прогнози ===

with tabs[0]: st.title("Стойностни залози – Прогнози за днес") st.caption("Кликни на бутона, за да добавиш залог")

for i, row in enumerate(value_bets):
    bg = STYLE_MAP.get(row["Сигурност"], "#ffffff")
    with st.container(border=True):
        st.markdown(f"""
            <div style='background-color: {bg}; padding: 10px; border-radius: 10px;'>
            <strong>{row['Мач']}</strong><br>
            Пазар: {row['Пазар']} | Коефициент: {row['Коефициент']:.2f} | Value: {row['Value %']}% | Час: {row['Начален час']}<br>
            Сигурност: {row['Сигурност']} от 5
            </div>
        """, unsafe_allow_html=True)

        bet = round(st.session_state["balance"] * 0.05, -1)
        if st.button(f"Залог {bet} лв", key=f"bet_{i}"):
            st.session_state["history"].append({
                "Мач": row["Мач"],
                "Пазар": row["Пазар"],
                "Коефициент": row["Коефициент"],
                "Сума": bet,
                "Печалба": round((row["Коефициент"] - 1) * bet, 2),
                "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Статус": "Предстои",
                "Начален час": row["Начален час"]
            })
            st.success(f"Заложено {bet} лв на {row['Мач']} – {row['Пазар']}")

=== TAB 2: История ===

with tabs[1]: st.header("История на залозите") history_df = pd.DataFrame(st.session_state["history"])

if not history_df.empty:
    now = datetime.now()
    for row in st.session_state["history"]:
        start_time = datetime.strptime(row["Начален час"], "%Y-%m-%d %H:%M")
        if row["Статус"] == "Предстои" and start_time < now:
            row["Статус"] = "Очаква резултат"

    history_df = pd.DataFrame(st.session_state["history"])

    def color_row(row):
        return [f"background-color: {STATUS_COLORS.get(row['Статус'], '#ffffff')}" for _ in row]

    st.dataframe(history_df.style.apply(color_row, axis=1), use_container_width=True)

    total_staked = history_df["Сума"].sum()
    total_profit = history_df["Печалба"].where(history_df["Статус"] == "Познат", 0).sum() - \
                   history_df["Сума"].where(history_df["Статус"] == "Грешен", 0).sum()
    roi = (total_profit / total_staked) * 100 if total_staked else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Залози", len(history_df))
    col2.metric("Нетна печалба", f"{total_profit:.2f} лв")
    col3.metric("ROI", f"{roi:.2f}%")

    if st.button("Запази историята"):
        pd.DataFrame(st.session_state["history"]).to_csv("history.csv", index=False)
        st.success("Историята е запазена.")
else:
    st.info("Няма още заложени мачове.")

=== TAB 3: Графики ===

with tabs[2]: st.header("Графики на печалбата") history_df = pd.DataFrame(st.session_state["history"]) if not history_df.empty: history_df["Дата"] = pd.to_datetime(history_df["Дата"]) history_df = history_df.sort_values("Дата") history_df["Натрупана печалба"] = ( history_df.apply( lambda r: r["Печалба"] if r["Статус"] == "Познат" else (-r["Сума"] if r["Статус"] == "Грешен" else 0), axis=1 ).cumsum() ) daily_profit = history_df.groupby(history_df["Дата"].dt.date)["Натрупана печалба"].last()

fig, ax = plt.subplots()
    ax.plot(daily_profit.index, daily_profit.values, marker="o", color="green")
    ax.set_title("Натрупана печалба по дни")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Печалба (лв)")
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)
else:
    st.info("Няма данни за графика.")

=== TAB 4: Настройки ===

with tabs[3]: st.header("Настройки на системата") new_balance = st.number_input("Начална банка", min_value=100, value=st.session_state["balance"], step=10) if st.button("Запази нова банка"): st.session_state["balance"] = new_balance st.success("Новата банка е запазена!") st.rerun()

