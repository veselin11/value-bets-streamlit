import streamlit as st import pandas as pd import random from datetime import datetime

st.set_page_config(page_title="Стойностни залози - Премачове", layout="wide")

--- Фиктивни данни ---

leagues = ["Английска Висша лига", "Испанска Ла Лига", "Италианска Серия А"] matches_data = [ {"league": random.choice(leagues), "home": f"Отбор {i}", "away": f"Съперник {i}", "odds": round(random.uniform(1.8, 3.5), 2), "value": round(random.uniform(5, 20), 1), "prob": round(random.uniform(40, 70), 1)} for i in range(1, 21) ]

--- Session State ---

if "bank" not in st.session_state: st.session_state.bank = 500.0 if "target_profit" not in st.session_state: st.session_state.target_profit = 150.0 if "bet_history" not in st.session_state: st.session_state.bet_history = []

--- Sidebar: Настройки ---

st.sidebar.title("Настройки") st.session_state.bank = st.sidebar.number_input("Начална банка (лв)", value=st.session_state.bank, step=10.0) st.session_state.target_profit = st.sidebar.number_input("Целева печалба (лв)", value=st.session_state.target_profit, step=10.0)

--- Tabs ---

tabs = st.tabs(["Прогнози", "История", "Статистика"])

--- Tab: Прогнози ---

with tabs[0]: st.title("Стойностни залози - Премачове") st.caption("Извличане на стойностни залози от API в реално време")

selected_league = st.selectbox("Избери първенство", ["Всички"] + leagues)

# Филтриране по първенство
filtered_matches = [m for m in matches_data if selected_league == "Всички" or m["league"] == selected_league]

for match in filtered_matches:
    with st.expander(f"{match['home']} vs {match['away']} - {match['league']}"):
        st.markdown(f"**Коефициент:** {match['odds']}")
        st.markdown(f"**Оценена вероятност:** {match['prob']}%")
        st.markdown(f"**Value (%):** {match['value']}")
        
        stake = round((st.session_state.bank / st.session_state.target_profit) * match['value'], 2)
        st.markdown(f"**Препоръчан залог:** {stake:.2f} лв")
        
        if st.button(f"Залагай на {match['home']} vs {match['away']}", key=f"bet_{match['home']}_{match['away']}"):
            bet = {
                "datetime": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "match": f"{match['home']} vs {match['away']}",
                "odds": match['odds'],
                "stake": stake,
                "value": match['value'],
                "result": "?"
            }
            st.session_state.bet_history.append(bet)
            st.success(f"Залогът е добавен към историята")

--- Tab: История ---

with tabs[1]: st.subheader("История на залозите") if st.session_state.bet_history: df_history = pd.DataFrame(st.session_state.bet_history) edited_df = st.data_editor(df_history, num_rows="dynamic", key="edit_history") st.session_state.bet_history = edited_df.to_dict("records") else: st.info("Все още няма направени залози.")

--- Tab: Статистика ---

with tabs[2]: st.subheader("Статистика") history = st.session_state.bet_history if history: total_bets = len(history) won = sum(1 for b in history if b['result'] == 'Печели') lost = sum(1 for b in history if b['result'] == 'Губи') profit = sum((b['odds'] - 1) * b['stake'] if b['result'] == 'Печели' else -b['stake'] for b in history if b['result'] != '?') roi = (profit / sum(b['stake'] for b in history if b['result'] != '?')) * 100 if history else 0 avg_value = sum(b['value'] for b in history) / total_bets

st.metric("Общ брой залози", total_bets)
    st.metric("Печеливши / Губещи", f"{won} / {lost}")
    st.metric("Нетна печалба (лв)", f"{profit:.2f}")
    st.metric("ROI (%)", f"{roi:.1f}%")
    st.metric("Среден value (%)", f"{avg_value:.1f}%")
else:
    st.info("Няма налична статистика.")

