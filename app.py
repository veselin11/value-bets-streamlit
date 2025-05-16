import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode

# === Сесийна инициализация ===
if "history" not in st.session_state:
    st.session_state["history"] = []
if "balance" not in st.session_state:
    st.session_state["balance"] = 500.0

# === Примерни прогнози ===
value_bets = [
    {"Мач": "Барселона - Реал", "Пазар": "1Х", "Коефициент": 2.10, "Value %": 15, "Начален час": "22:00"},
    {"Мач": "Арсенал - Челси", "Пазар": "Над 2.5", "Коефициент": 1.85, "Value %": 12, "Начален час": "21:30"},
    {"Мач": "Байерн - Борусия", "Пазар": "Х2", "Коефициент": 3.25, "Value %": 18, "Начален час": "19:45"},
    {"Мач": "Интер - Милан", "Пазар": "1", "Коефициент": 2.50, "Value %": 22, "Начален час": "20:00"},
]

# === Функция за цветова индикация на сигурност ===
def get_confidence_color(value_percent):
    if value_percent >= 20:
        return "#b2f2bb"  # светло зелено
    elif value_percent >= 15:
        return "#ffe066"  # жълто
    else:
        return "#ffa8a8"  # светло червено

# === ТАБОВЕ ===
tabs = st.tabs(["Прогнози", "История", "Статистика"])

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Днес")
    st.caption("Кликни на бутона за залог, за да го добавиш в историята.")

    df = pd.DataFrame(value_bets)

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

    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])

        # Добавяме ID и колона за изтриване
        df = df.reset_index().rename(columns={"index": "ID"})
        df["Изтрий"] = ""

        # JS код за бутон "изтрий"
        delete_button_code = JsCode("""
        function(params) {
            return `<button style="background-color: transparent; color: red; font-weight: bold; border: none; cursor: pointer;">x</button>`;
        }
        """)

        # JS за зареждане на грида
        js_delete_func = JsCode("""
        function deleteRow(rowIndex) {
            const api = window.gridOptions.api;
            const rowNode = api.getDisplayedRowAtIndex(rowIndex);
            api.applyTransaction({ remove: [rowNode.data] });
        }
        """)

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(resizable=True, filter=True, sortable=True)
        gb.configure_column("Изтрий", header_name="", cellRenderer=delete_button_code, width=50)
        gb.configure_column("Статус", editable=True, cellEditor="agSelectCellEditor",
                            cellEditorParams={"values": ["Предстои", "Печели", "Губи"]})

        # Цветове за статус
        status_cell_style = JsCode("""
        function(params) {
            if (params.value == 'Печели') {
                return {'color': 'green', 'fontWeight': 'bold'};
            } else if (params.value == 'Губи') {
                return {'color': 'red', 'fontWeight': 'bold'};
            } else {
                return {'color': 'gray'};
            }
        }
        """)
        gb.configure_column("Статус", cellStyle=status_cell_style)

        gb.configure_grid_options(domLayout='normal')
        gb.configure_grid_options(onGridReady=JsCode("function(params) { window.gridOptions = params; }"))
        gb.configure_grid_options(components={"deleteRow": js_delete_func})

        grid_response = AgGrid(
            df,
            gridOptions=gb.build(),
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.NO_UPDATE,
            fit_columns_on_grid_load=True,
            height=500,
            theme="streamlit"
        )

        # Обновяваме историята
        updated_df = grid_response["data"].drop(columns=["ID", "Изтрий"])
        st.session_state["history"] = updated_df.to_dict("records")

        # Експорт бутон
        st.download_button("Изтегли като Excel", data=updated_df.to_excel(index=False), file_name="istoriya.xlsx")
        st.download_button("Изтегли като CSV", data=updated_df.to_csv(index=False), file_name="istoriya.csv")

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
