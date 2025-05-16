import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO

st.set_page_config(page_title="Value Bets App", layout="wide")
st.markdown("""
    <style>
    .transparent-card {
        background-color: rgba(255, 255, 255, 0.8) !important;
        padding: 1rem;
        border-radius: 0.75rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .ag-theme-streamlit .ag-root-wrapper {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Примерни прогнози (симулация)
example_bets = pd.DataFrame([
    {"Мач": "Тим А vs Тим Б", "Пазар": "1X2", "Залог": "1", "Коефициент": 2.1, "Value %": 15.3},
    {"Мач": "Тим В vs Тим Г", "Пазар": "Над/Под 2.5", "Залог": "Над 2.5", "Коефициент": 1.95, "Value %": 12.1},
    {"Мач": "Тим Д vs Тим Е", "Пазар": "Хендикап", "Залог": "-1 Тим Д", "Коефициент": 2.4, "Value %": 18.7},
])

# История на залози
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Мач", "Пазар", "Залог", "Коефициент", "Value %", "Статус", "Печалба"])

st.title("Value Bets Приложение")
tabs = st.tabs(["Прогнози", "История", "Статистика"])

with tabs[0]:
    st.subheader("Прогнози за днес")
    with st.container():
        gb = GridOptionsBuilder.from_dataframe(example_bets)
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            example_bets,
            gridOptions=grid_options,
            height=300,
            theme="streamlit",
            fit_columns_on_grid_load=True
        )

        selected = grid_response["selected_rows"]

        if st.button("Заложи избраните"):
            for row in selected:
                row_data = row.copy()
                row_data["Статус"] = "Отворен"
                row_data["Печалба"] = None
                st.session_state.history = pd.concat([
                    st.session_state.history,
                    pd.DataFrame([row_data])
                ], ignore_index=True)
            st.success(f"Добавени {len(selected)} залога към историята.")

with tabs[1]:
    st.subheader("История на залозите")
    if st.session_state.history.empty:
        st.info("Няма налични залози.")
    else:
        gb = GridOptionsBuilder.from_dataframe(st.session_state.history)
        gb.configure_pagination(enabled=True)
        gb.configure_default_column(resizable=True, filter=True, sortable=True)
        grid_options = gb.build()

        AgGrid(
            st.session_state.history,
            gridOptions=grid_options,
            height=400,
            theme="streamlit",
            fit_columns_on_grid_load=True,
        )

        # Изтегляне като Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.history.to_excel(writer, index=False)
            writer.save()
            processed_data = output.getvalue()

        st.download_button(
            label="Изтегли като Excel",
            data=processed_data,
            file_name="istoriya.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with tabs[2]:
    st.subheader("Статистика")
    if st.session_state.history.empty:
        st.info("Няма данни за статистика.")
    else:
        total_bets = len(st.session_state.history)
        closed_bets = st.session_state.history.dropna(subset=["Печалба"])
        profit = closed_bets["Печалба"].sum()
        win_rate = (closed_bets["Печалба"] > 0).mean() * 100 if not closed_bets.empty else 0
        avg_value = st.session_state.history["Value %"].mean()

        st.metric("Общ брой залози", total_bets)
        st.metric("Обща печалба", f"{profit:.2f} лв")
        st.metric("Успеваемост", f"{win_rate:.1f}%")
        st.metric("Среден Value %", f"{avg_value:.1f}%")
                                    
