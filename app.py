def main():
    st.set_page_config(page_title="Smart Bet Advisor", layout="wide")
    st.title("⚽ Smart Betting Analyzer")

    matches = get_live_odds()
    if not matches:
        st.warning("❗ Няма налични мачове за днес.")
        return

    match_names = []
    for m in matches:
        try:
            home = m["bookmakers"][0]["markets"][0]["outcomes"][0]["name"]
            away = m["bookmakers"][0]["markets"][0]["outcomes"][1]["name"]
            match_names.append(f"{home} vs {away}")
        except:
            continue

    selected_match = st.selectbox("Избери мач:", match_names, index=0)

    match = None
    for m in matches:
        try:
            if selected_match == f"{m['bookmakers'][0]['markets'][0]['outcomes'][0]['name']} vs {m['bookmakers'][0]['markets'][0]['outcomes'][1]['name']}":
                match = m
                break
        except:
            continue

    if not match:
        st.error("⚠ Проблем при избора на мач.")
        return

    home_team = match["bookmakers"][0]["markets"][0]["outcomes"][0]["name"]
    away_team = match["bookmakers"][0]["markets"][0]["outcomes"][1]["name"]

    # Проверка за наличност в TEAM_ID_MAPPING
    if home_team not in TEAM_ID_MAPPING or away_team not in TEAM_ID_MAPPING:
        st.error(f"Един отбор не е в TEAM_ID_MAPPING: {home_team}, {away_team}")
        st.info("Моля, добави ги ръчно в TEAM_ID_MAPPING в кода.")
        return

    # Вземане на статистики
    home_raw_stats = get_team_stats(home_team)
    away_raw_stats = get_team_stats(away_team)

    if home_raw_stats is None or away_raw_stats is None:
        st.error("Няма налични статистики за един от отборите.")
        return

    home_stats = get_team_stats_data(home_raw_stats, is_home=True)
    away_stats = get_team_stats_data(away_raw_stats, is_home=False)

    # Извличане на коефициенти
    try:
        best_odds = {
            "home": match["bookmakers"][0]["markets"][0]["outcomes"][0]["price"],
            "away": match["bookmakers"][0]["markets"][0]["outcomes"][1]["price"],
            "draw": next(o["price"] for o in match["bookmakers"][0]["markets"][0]["outcomes"] if o["name"].lower() == "draw")
        }
    except:
        best_odds = {"home": 1.5, "draw": 4.0, "away": 6.0}

    # Изчисления
    prob_home, prob_draw, prob_away = calculate_poisson_probabilities(
        home_stats["avg_goals"],
        away_stats["avg_goals"]
    )

    value_bets = calculate_value_bets(
        (prob_home, prob_draw, prob_away),
        best_odds
    )

    # UI Tabs
    tab1, tab2, tab3 = st.tabs(["Match Analysis", "Team History", "AI Predictions"])

    with tab1:
        cols = st.columns(3)
        outcomes = [
            ("🏠 Home Win", prob_home, value_bets["home"], best_odds["home"]),
            ("⚖ Draw", prob_draw, value_bets["draw"], best_odds["draw"]),
            ("✈ Away Win", prob_away, value_bets["away"], best_odds["away"])
        ]
        for col, (title, prob, value, odds) in zip(cols, outcomes):
            with col:
                st.subheader(title)
                st.metric("Probability", f"{prob*100:.1f}%")
                st.metric("Best Odds", f"{odds:.2f}")
                value_color = "green" if value > 0 else "red"
                st.markdown(f"**Value:** <span style='color:{value_color}'>{(value*100):.1f}%</span>", unsafe_allow_html=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Last 10 Matches - {home_team}")
            for m in reversed(home_raw_stats[-10:]):
                score = m["score"]["fullTime"]
                st.caption(f"{format_date(m['utcDate'])} | {score['home']}-{score['away']}")
        with col2:
            st.subheader(f"Last 10 Matches - {away_team}")
            for m in reversed(away_raw_stats[-10:]):
                score = m["score"]["fullTime"]
                st.caption(f"{format_date(m['utcDate'])} | {score['away']}-{score['home']}")

    with tab3:
        if st.button("Генерирай AI прогноза"):
            with st.spinner("Анализ..."):
                prediction = predict_with_ai(home_stats, away_stats)
            if prediction is not None:
                st.subheader("🤖 AI Prediction Results")
                cols = st.columns(3)
                labels = ["Home Win", "Draw", "Away Win"]
                colors = ["#4CAF50", "#FFC107", "#2196F3"]
                for col, label, prob, color in zip(cols, labels, prediction, colors):
                    with col:
                        st.markdown(f"<h3 style='color:{color}'>{label}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<h2>{prob*100:.1f}%</h2>", unsafe_allow_html=True)
                st.progress(max(prediction))
