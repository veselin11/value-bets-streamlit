import streamlit as st
from datetime import datetime, timedelta
import random
import pytz
import pandas as pd

st.set_page_config(page_title="Стойностни залози", layout="wide")
tabs = st.tabs(["Прогнози", "История", "Настройки"])

local_tz = pytz.timezone("Europe/Sofia")
today = datetime.now(local_tz).date()

# Инициализиране на сесия за история
if "history" not in st.session_state:
    st.session_state.history = []

# === ТАБ 1: Прогнози ===
with tabs[0]:
    st.title("Стойностни залози – Фиктивни данни за тестване")
    st.caption("Тези данни са генерирани временно за тестове")

    # Задаване на фиктивни мачове
    fake_matches = []
    teams = [("Real Madrid", "Barcelona"), ("Man City", "Liverpool"),
             ("Juventus", "Inter"), ("Bayern", "Dortmund"), ("PSG", "Lyon")]

    for home, away in teams:
        kickoff = datetime.now(local_tz) + timedelta(minutes=random.randint(30, 300))
        odds = {
            "home": round(random.uniform(1.8, 3.5), 2),
            "draw": round(random.uniform(3.0, 4.5), 2),
            "away": round(random.uniform(1.8, 3.5), 2),
            "gg": round(random.uniform(1.6, 2.5), 2),
            "over_2.5": round(random.uniform(1.7, 2.4), 2)
        }

        for market, price in odds.items():
            fair_prob = 1 / price
            value = price * fair_prob  # Проста логика
            if value > 1.05:
                fake_matches.append({
                    "Мач": f"{home} vs {away}",
                    "Пазар": market.upper(),
                    "Коефициент": price,
                    "Начален час": kickoff.strftime("%H:%M"),
                    "Value %": round((value - 1) * 100, 2),
                    "Заложи": False
                })

    if fake_matches:
        df = pd.DataFrame(fake_matches)
        df = df.sort_values(by="Value %", ascending=False)

        st.markdown("### Избери залози")
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            column_config={
                "Заложи": st.column_config.CheckboxColumn("Заложи"),
                "Коефициент": st.column_config.NumberColumn(format="%.2f"),
                "Value %": st.column_config.NumberColumn(format="%.2f")
            },
            key="editor"
        )

        # Обработка на избраните залози
        for i, row in edited_df.iterrows():
            if row["Заложи"]:
                bet_amount = 10  # фиксирана сума
                outcome = random.choice(["win", "lose"])
                profit = (row["Коефициент"] * bet_amount - bet_amount) if outcome == "win" else -bet_amount

                st.session_state.history.append({
                    "Мач": row["Мач"],
                    "Пазар": row["Пазар"],
                    "Коефициент": row["Коефициент"],
                    "Стойност %": row["Value %"],
                    "Сума": bet_amount,
                    "Резултат": "Печалба" if outcome == "win" else "Загуба",
                    "Печалба": round(profit, 2),
                    "Час": row["Начален час"]
                })

# === ТАБ 2: История ===
with tabs[1]:
    st.header("История на залози")
    if st.session_state.history:
        df_hist = pd.DataFrame(st.session_state.history)
        total_profit = df_hist["Печалба"].sum()
        st.metric("Обща печалба", f"{total_profit:.2f} лв")
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("Все още няма направени залози.")

# === ТАБ 3: Настройки ===
with tabs[2]:
    st.header("Настройки")
    st.write("Тук ще се появят настройки за избор на лиги, цели и др. – в разработка.")
