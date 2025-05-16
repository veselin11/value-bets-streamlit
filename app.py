import streamlit as st
import pandas as pd
import datetime
import io

# Конфигурация на страницата
st.set_page_config(page_title="Value Betting Tracker", layout="wide")

# Инициализиране на сесията
if "history" not in st.session_state:
    st.session_state["history"] = []

# Навигация
tabs = st.tabs(["Прогнози", "История", "Статистика"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.header("Днешни стойностни прогнози")

    example_predictions = [
        {"Мач": "Ливърпул - Челси", "Пазар": "1X2 - Победа Ливърпул", "Коефициент": 2.10, "Value %": 12.5},
        {"Мач": "Байерн - Дортмунд", "Пазар": "Голове Над 2.5", "Коефициент": 1.80, "Value %": 9.1},
        {"Мач": "Ювентус - Милан", "Пазар": "Двоен шанс Х2", "Коефициент": 2.30, "Value %": 11.0},
    ]

    df_preds = pd.DataFrame(example_predictions)
    st.dataframe(df_preds, use_container_width=True)

    st.markdown("### Добави залог към историята")
    with st.form("add_bet_form"):
        col1, col2, col3 = st.columns(3)
        match = col1.selectbox("Мач", [p["Мач"] for p in example_predictions])
        market = col2.text_input("Пазар", value="1X2 - Победа")
        odds = col3.number_input("Коефициент", value=2.00, step=0.01)
        stake = st.number_input("Сума на залога (лв)", value=10, step=1)
        date = st.date_input("Дата", value=datetime.date.today())

        submitted = st.form_submit_button("Добави")
        if submitted:
            st.session_state["history"].append({
                "Мач": match,
                "Пазар": market,
                "Коефициент": odds,
                "Сума": stake,
                "Печалба": 0.00,
                "Дата": date.strftime("%Y-%m-%d"),
                "Статус": "-"
            })
            st.success("Залогът е добавен!")

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залозите")
    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])

        st.write("Маркирай изхода на мачовете директно в таблицата:")

        for i in range(len(history_df)):
            cols = st.columns([3, 1.5, 1.2, 1.2, 1.2, 1.5, 2])
            cols[0].write(history_df.at[i, "Мач"])
            cols[1].write(history_df.at[i, "Пазар"])
            cols[2].write(f"{history_df.at[i, 'Коефициент']:.2f}")
            cols[3].write(f"{history_df.at[i, 'Сума']:.0f} лв")
            cols[4].write(f"{history_df.at[i, 'Печалба']:.2f} лв")
            cols[5].write(history_df.at[i, "Дата"])

            new_status = cols[6].selectbox(
                "", ["-", "Печели", "Губи"],
                index=["-", "Печели", "Губи"].index(history_df.at[i, "Статус"]) if history_df.at[i, "Статус"] in ["Печели", "Губи"] else 0,
                key=f"inline_result_{i}"
            )

            if new_status == "Печели" and history_df.at[i, "Статус"] != "Печели":
                history_df.at[i, "Статус"] = "Печели"
                history_df.at[i, "Печалба"] = round((history_df.at[i, "Коефициент"] - 1) * history_df.at[i, "Сума"], 2)
            elif new_status == "Губи" and history_df.at[i, "Статус"] != "Губи":
                history_df.at[i, "Статус"] = "Губи"
                history_df.at[i, "Печалба"] = -history_df.at[i, "Сума"]

        st.session_state["history"] = history_df.to_dict("records")

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
        st.download_button("Свали Excel файл", data=excel_data, file_name="istoriya_zalozi.xlsx")
    else:
        st.info("Няма още заложени мачове.")

# === ТАБ 3: Статистика (предстояща функция) ===
with tabs[2]:
    st.header("Обобщена статистика (в разработка)")
    st.info("Скоро ще бъде добавен графичен анализ по дни, филтри, пазари и други.")
