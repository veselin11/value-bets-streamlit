import streamlit as st
import pandas as pd
import random
from datetime import datetime

st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

# Сесийни променливи
if "history" not in st.session_state:
    st.session_state["history"] = []

# Фиктивни данни за мачове
fake_matches = [
    {
        "home": "Liverpool",
        "away": "Manchester United",
        "start": "20:00",
        "markets": {
            "1X2": {"home": 2.2, "draw": 3.4, "away": 3.1},
            "GG": {"yes": 1.8, "no": 2.0},
            "Over/Under 2.5": {"over": 1.9, "under": 2.0}
        }
    },
    {
        "home": "Barcelona",
        "away": "Atletico Madrid",
        "start": "22:00",
        "markets": {
            "1X2": {"home": 1.8, "draw": 3.8, "away": 4.2},
            "GG": {"yes": 1.7, "no": 2.1},
            "Over/Under 2.5": {"over": 2.0, "under": 1.9}
        }
    }
]

# Настройки
with tabs[2]:
    st.header("Настройки")
    target_profit = st.number_input("Целева печалба (напр. 150 лв за 5 дни)", value=150)
    starting_bank = st.number_input("Начална банка", value=500)
    days = st.number_input("Брой дни за изпълнение", value=5)
    bets_per_day = st.number_input("Очаквани залози на ден", value=5)
    st.success("Настройките са запазени.")

# Прогнози
with tabs[0]:
    st.title("Стойностни залози – Примерни мачове")
    st.caption("Фиктивни данни за тестване")

    total_bets = bets_per_day * days
    stake = round((target_profit / total_bets) * 10) / 10  # кръгло на 10

    st.write(f"Препоръчителна сума на залог: **{round(stake, -1)} лв**")

    for match in fake_matches:
        st.subheader(f"{match['home']} vs {match['away']} ({match['start']})")
        for market_name, outcomes in match["markets"].items():
            st.markdown(f"**{market_name}**", help="Избери пазар за залог")
            cols = st.columns(len(outcomes))
            for i, (outcome, odd) in enumerate(outcomes.items()):
                with cols[i]:
                    if st.button(f"{outcome} ({odd})", key=f"{match['home']}_{match['away']}_{market_name}_{outcome}"):
                        st.session_state["history"].append({
                            "Мач": f"{match['home']} vs {match['away']}",
                            "Пазар": market_name,
                            "Избор": outcome,
                            "Коефициент": odd,
                            "Сума": round(stake, -1),
                            "Печалба": round(round(stake, -1) * odd, 2),
                            "Час": match["start"],
                            "Статус": "Очаква се"
                        })
                        st.success(f"Залог поставен: {outcome} @ {odd}")

# История
with tabs[1]:
    st.header("История на залозите")

    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Добави произволни резултати"):
                for bet in st.session_state["history"]:
                    bet["Статус"] = random.choice(["Печалба", "Загуба"])

        profit = sum([b["Печалба"] - b["Сума"] if b["Статус"] == "Печалба" else -b["Сума"] for b in st.session_state["history"]])
        wins = sum(1 for b in st.session_state["history"] if b["Статус"] == "Печалба")
        total = len(st.session_state["history"])
        roi = (profit / (sum(b["Сума"] for b in st.session_state["history"])) * 100) if total else 0

        st.metric("Обща печалба", f"{profit:.2f} лв")
        st.metric("Успеваемост", f"{(wins/total)*100:.1f}%" if total else "0%")
        st.metric("ROI", f"{roi:.2f}%")

        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("Все още няма направени залози.")
