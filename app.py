import streamlit as st
from datetime import datetime
import pandas as pd
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Стойностни залози", layout="wide")

# Сесийна инициализация
if "history" not in st.session_state:
    st.session_state["history"] = []

if "balance" not in st.session_state:
    st.session_state["balance"] = 500

# Примерни залози за днес
value_bets = [
    {"Мач": "Inter vs Milan", "Пазар": "1", "Коефициент": 2.25, "Value %": 8.2, "Начален час": "21:45"},
    {"Мач": "Liverpool vs Man City", "Пазар": "ГГ", "Коефициент": 1.85, "Value %": 5.6, "Начален час": "22:00"},
    {"Мач": "Leverkusen vs Bayern", "Пазар": "Над 2.5", "Коефициент": 2.05, "Value %": 3.8, "Начален час": "20:30"},
]

# Стил за сигурност
def get_security_style(value_percent):
    if value_percent >= 7.5:
        return "Висока", "#d1fae5"  # зелено
    elif value_percent >= 5:
        return "Средна", "#fef9c3"  # жълто
    else:
        return "Ниска", "#f3f4f6"  # сиво

tabs = st.tabs(["Прогнози", "История", "Графики", "Настройки"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Днешни стойностни прогнози")
    st.caption("Избери сума за залог, за да запишеш в историята")

    df = pd.DataFrame(value_bets)

    for i, row in df.iterrows():
        сигурност, цвят = get_security_style(row["Value %"])
        with st.container(border=True):
            st.markdown(
                f"""<div style="background-color:{цвят}; padding: 10px; border-radius: 10px;">
                <b>{row['Мач']}</b><br>
                Пазар: {row['Пазар']}<br>
                Коефициент: {row['Коефициент']:.2f}<br>
                Value: {row['Value %']}%<br>
                Сигурност: <b>{сигурност}</b><br>
                Начален час: {row['Начален час']}
                </div>""",
                unsafe_allow_html=True
            )
            suggested_bet = round(st.session_state["balance"] * 0.05, -1)
            if st.button(f"Залог {suggested_bet} лв", key=f"bet_{i}"):
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
        # Цветове по статус
        def color_row(row):
            if row["Статус"] == "Печеливш":
                return ["background-color: #dcfce7"] * len(row)
            elif row["Статус"] == "Губещ":
                return ["background-color: #fee2e2"] * len(row)
            else:
                return ["background-color: #e0f2fe"] * len(row)

        styled_df = history_df.style.apply(color_row, axis=1)
        st.dataframe(styled_df, use_container_width=True)

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
        st.download_button("Свали като Excel", data=excel_data, file_name="istoriya_zalozi.xlsx")
    else:
        st.info("Няма още залози.")

# === ТАБ 3: Графики ===
with tabs[2]:
    st.header("Графика на печалбата")
    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])
        history_df["Натрупана печалба"] = history_df["Печалба"].cumsum()
        history_df["Дата"] = pd.to_datetime(history_df["Дата"])

        fig, ax = plt.subplots()
        ax.plot(history_df["Дата"], history_df["Натрупана печалба"], marker="o", linestyle="-", color="green")
        ax.set_title("Натрупана печалба")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Печалба (лв)")
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
        st.success("Новата банка е запазена!")
        st.rerun()
