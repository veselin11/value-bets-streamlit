import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

st.set_page_config(layout="wide")

# Инициализация
if "history" not in st.session_state:
    st.session_state["history"] = []

# Интерфейс с табове
tabs = st.tabs(["Прогнози", "История"])

with tabs[0]:
    st.title("Прогнози за стойностни залози")
    # Примерни прогнози
    example_bets = [
        {"Мач": "Барселона - Реал Мадрид", "Пазар": "1X2", "Избор": "1", "Коеф": 2.5, "Value %": 18.2, "Статус": ""},
        {"Мач": "Ливърпул - Ман Сити", "Пазар": "Над/Под", "Избор": "Над 2.5", "Коеф": 1.9, "Value %": 12.6, "Статус": ""},
        {"Мач": "Байерн - Дортмунд", "Пазар": "Хендикап", "Избор": "-1", "Коеф": 3.1, "Value %": 22.4, "Статус": ""}
    ]

    for i, bet in enumerate(example_bets):
        with st.container():
            cols = st.columns([3, 2, 2, 1, 1])
            cols[0].markdown(f"**{bet['Мач']}**")
            cols[1].markdown(f"{bet['Пазар']}: {bet['Избор']}")
            cols[2].markdown(f"Коеф: {bet['Коеф']}")
            cols[3].markdown(f"Value: {bet['Value %']}%")
            if cols[4].button("Залагай", key=f"bet_{i}"):
                st.session_state["history"].append(bet)
                st.success(f"Добавено: {bet['Мач']}")

with tabs[1]:
    st.title("История на залозите")

    if st.session_state["history"]:
        df = pd.DataFrame(st.session_state["history"])

        df = df.reset_index().rename(columns={"index": "ID"})
        df["Печели"] = ""
        df["Губи"] = ""
        df["Изтрий"] = ""

        # JS бутони за действия
        action_button = lambda emoji: JsCode(f"""
            function(params) {{
                return `<button style=\"background-color: transparent; font-size: 18px; border: none; cursor: pointer;\">{emoji}</button>`;
            }}
        """)

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(resizable=True, filter=True, sortable=True, wrapText=True, autoHeight=True)

        # Добавяне на визуални бутони
        gb.configure_column("Печели", header_name="", cellRenderer=action_button("✅"), width=60)
        gb.configure_column("Губи", header_name="", cellRenderer=action_button("❌"), width=60)
        gb.configure_column("Изтрий", header_name="", cellRenderer=action_button("✖"), width=60)

        # Стил по статус
        row_style = JsCode("""
        function(params) {
            if (params.data.Статус == 'Печели') {
                return { 'backgroundColor': '#d3f9d8' };
            } else if (params.data.Статус == 'Губи') {
                return { 'backgroundColor': '#ffe3e3' };
            } else {
                return { 'backgroundColor': '#f1f3f5' };
            }
        }
        """)

        gb.configure_grid_options(getRowStyle=row_style)
        gb.configure_grid_options(domLayout='autoHeight', onCellClicked=JsCode("""
            function(e) {
                if (e.colDef.field === 'Печели') {
                    e.node.setDataValue('Статус', 'Печели');
                } else if (e.colDef.field === 'Губи') {
                    e.node.setDataValue('Статус', 'Губи');
                } else if (e.colDef.field === 'Изтрий') {
                    const api = e.api;
                    const row = e.node.data;
                    api.applyTransaction({ remove: [row] });
                }
            }
        """))

        grid_response = AgGrid(
            df,
            gridOptions=gb.build(),
            allow_unsafe_jscode=True,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True,
            height=600,
            theme="streamlit"
        )

        # Обновяване
        updated_df = grid_response["data"].drop(columns=["ID", "Печели", "Губи", "Изтрий"])
        st.session_state["history"] = updated_df.to_dict("records")

        st.download_button("Изтегли като Excel", data=updated_df.to_excel(index=False), file_name="istoriya.xlsx")
        st.download_button("Изтегли като CSV", data=updated_df.to_csv(index=False), file_name="istoriya.csv")
    else:
        st.info("Няма още запазени залози.")
    
