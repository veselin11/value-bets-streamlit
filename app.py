import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

if "history" not in st.session_state:
    st.session_state["history"] = []

# Фиктивни мачове
fake_matches = [
    {
        "home": "Liverpool",
        "away": "Man Utd",
        "start": "20:00",
        "markets": {
            "1X2": {"home": 2.1, "draw": 3.3, "away": 3.4},
            "GG": {"yes": 1.8, "no": 2.0},
            "Over/Under 2.5": {"over": 1.95, "under": 1.9},
            "Over/Under 1.5": {"over": 1.4, "under": 2.8},
            "Exact Score": {"1-0": 7.5, "2-1": 8.0, "2-2": 12.0}
        }
    },
    {
        "home": "Barcelona",
        "away": "Atletico",
        "start": "22:00",
        "markets": {
            "1X2": {"home": 1.9, "draw": 3.6, "away": 4.1},
            "GG": {"yes": 1.7, "no": 2.2},
            "Over/Under 2.5": {"over": 2.0, "under": 1.85},
            "Over/Under 1.5": {"over": 1.5, "under": 2.5},
            "Exact Score": {"1-0": 6.5, "2-1": 7.2, "3-2": 15.0}
        }
    }
]

# Настройки
with tabs[2]:
    st.header("Настройки")
    target_profit = st.number_input("Целева печалба (лв)", value=150)
    starting_bank = st.number_input("Начална банка (лв)", value=500)
    days = st.number_input("Брой дни за постигане", value=5)
    bets_per_day = st.number_input("Брой залози на ден", value=5)

    total_bets = days * bets_per_day
    stake = round((target_profit / total_bets) / 10) * 10

    st.success(f"Препоръчителна сума на залог: {stake} лв")

# Прогнози
with tabs[0]:
    st.title("Стойностни залози – Примерни мачове")

    for match in fake_matches:
        st.subheader(f"{match['home']} vs {match['away']} ({match['start']})")
        for market, options in match["markets"].items():
            st.markdown(f"**{market}**")
            cols = st.columns(len(options))
            for i, (opt, odd) in enumerate(options.items()):
                with cols[i]:
                    if st.button(f"{opt} ({odd})", key=f"{match['home']}_{market}_{opt}"):
                        st.session_state["history"].append({
                            "Мач": f"{match['home']} vs {match['away']}",
                            "Пазар": market,
                            "Избор": opt,
                            "Коефициент": odd,
                            "Сума": stake,
                            "Печалба": round(stake * odd, 2),
                            "Час": match["start"],
                            "Статус": "Очаква се"
                        })
                        st.success(f"Залог добавен: {opt} @ {odd}")

# История
with tabs[1]:
    st.header("История на залозите")

    if st.session_state["history"]:
        history_df = pd.DataFrame(st.session_state["history"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Симулирай резултати"):
                for bet in st.session_state["history"]:
                    if bet["Статус"] == "Очаква се":
                        bet["Статус"] = random.choices(["Печалба", "Загуба"], weights=[0.5, 0.5])[0]

        with col2:
            if st.button("Изчисти историята"):
                st.session_state["history"] = []

        profit = sum(b["Печалба"] - b["Сума"] if b["Статус"] == "Печалба" else -b["Сума"]
                     for b in st.session_state["history"])
        wins = sum(1 for b in st.session_state["history"] if b["Статус"] == "Печалба")
        total = len(st.session_state["history"])
        roi = (profit / (sum(b["Сума"] for b in st.session_state["history"])) * 100) if total else 0

        st.metric("Обща печалба", f"{profit:.2f} лв")
        st.metric("Успеваемост", f"{(wins / total) * 100:.1f}%")
        st.metric("ROI", f"{roi:.2f}%")

        st.dataframe(pd.DataFrame(st.session_state["history"]), use_container_width=True)
    else:
        st.info("Няма направени залози.")
