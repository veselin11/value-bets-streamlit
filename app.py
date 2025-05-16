import streamlit as st 
import pandas as pd from datetime 
import datetime

st.set_page_config(page_title="Value Bets", layout="wide") st.title("Value Bets Приложение")

Инициализация на състояние

if "history" not in st.session_state: st.session_state["history"] = [] if "bank" not in st.session_state: st.session_state["bank"] = 500.0

Табове: Прогнози | История | Статистика

tabs = st.tabs(["Прогнози", "История", "Статистика"])

=================== ТАБ 1: ПРОГНОЗИ ===================

with tabs[0]: st.subheader("Днешни стойностни прогнози") # Примерни прогнози (замени с реални) predictions = [ {"Мач": "Барселона - Реал Мадрид", "Коефициент": 2.5, "Вероятност": 0.55, "Стойност": 37, "Час": "22:00", "Пазар": "1X2", "Прогноза": "1"}, {"Мач": "Милан - Интер", "Коефициент": 3.2, "Вероятност": 0.4, "Стойност": 28, "Час": "21:45", "Пазар": "1X2", "Прогноза": "2"}, {"Мач": "Ливърпул - Ман Сити", "Коефициент": 1.9, "Вероятност": 0.6, "Стойност": 14, "Час": "20:00", "Пазар": "1X2", "Прогноза": "1"} ] df = pd.DataFrame(predictions)

for i, row in df.iterrows():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**{row['Мач']}**  ")
        st.markdown(f"Пазар: {row['Пазар']}  ")
        st.markdown(f"Прогноза: {row['Прогноза']}  ")
        st.markdown(f"Час: {row['Час']}")
    with col2:
        st.markdown(f"Коеф: **{row['Коефициент']}**")
        st.markdown(f"Вер: **{int(row['Вероятност']*100)}%**")
        st.markdown(f"Value: **{row['Стойност']}%**")
        if st.button(f"Залагай #{i+1}"):
            залог = round(st.session_state.bank * 0.05, 2)
            st.session_state.bank -= залог
            st.session_state.history.append({
                "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Мач": row['Мач'],
                "Прогноза": row['Прогноза'],
                "Коефициент": row['Коефициент'],
                "Залог": залог,
                "Статус": "Предстои",
                "Печалба": 0.0
            })

=================== ТАБ 2: ИСТОРИЯ ===================

with tabs[1]: st.subheader("История на залозите")

if len(st.session_state.history) == 0:
    st.info("Все още няма направени залози.")
else:
    df = pd.DataFrame(st.session_state.history)

    # Филтри
    st.markdown("### Таблица с филтри")
    selected_status = st.multiselect("Статус", ["Предстои", "Печели", "Губи"], default=["Предстои", "Печели", "Губи"])
    filtered_df = df[df["Статус"].isin(selected_status)]

    sort_by = st.selectbox("Сортирай по", ["Дата", "Печалба", "Коефициент"])
    filtered_df = filtered_df.sort_values(sort_by, ascending=False)

    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

=================== ТАБ 3: СТАТИСТИКА ===================

with tabs[2]: st.subheader("Статистика") df = pd.DataFrame(st.session_state.history) if df.empty: st.warning("Няма данни за статистика.") else: общо = len(df) спечелени = len(df[df["Статус"] == "Печели"]) загубени = len(df[df["Статус"] == "Губи"]) предстоящи = len(df[df["Статус"] == "Предстои"]) печалба = df["Печалба"].sum() roi = (печалба / df["Залог"].sum()) * 100 if df["Залог"].sum() > 0 else 0

col1, col2, col3 = st.columns(3)
    col1.metric("Общо залози", общо)
    col2.metric("Печалба (лв)", f"{печалба:.2f}")
    col3.metric("ROI", f"{roi:.1f}%")

    col4, col5, col6 = st.columns(3)
    col4.metric("Спечелени", спечелени)
    col5.metric("Загубени", загубени)
    col6.metric("Предстои", предстоящи)

=================== КОНТРОЛИ В ДОЛНАТА ЧАСТ ===================

st.sidebar.header("Настройки") ново_начало = st.sidebar.button("Изчисти всичко") if ново_начало: st.session_state.history = [] st.session_state.bank = 500.0

st.sidebar.markdown(f"Текуща банка: {st.session_state.bank:.2f} лв")

