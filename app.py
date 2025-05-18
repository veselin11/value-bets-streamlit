import streamlit as st
import requests

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

EUROPE_LEAGUES = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_russia_premier_league",
    "soccer_ukraine_premier_league",
    # махнати проблемни лиги:
    # "soccer_portugal_liga",
    # "soccer_turkey_superlig"
]

MARKETS = ["h2h", "totals", "both_teams_to_score"]

def fetch_odds(league):
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": ",".join(MARKETS),
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"Грешка при зареждане на {league}: {e}")
        return None

def calculate_value_bets(odds_data):
    value_bets = []
    for match in odds_data or []:
        teams = match.get('teams')
        commence_time = match.get('commence_time', '')
        league = match.get('sport_key', '')
        bookmakers = match.get('bookmakers', [])

        # Пресмятане на средни коефициенти за всеки пазар и избор на стойностни залози
        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                market_key = market.get('key')
                for outcome in market.get('outcomes', []):
                    odd = outcome.get('price')
                    name = outcome.get('name')

                    # Изчисляване на среден коефициент по пазар и залог
                    all_odds = []
                    for bm in bookmakers:
                        for m in bm.get('markets', []):
                            if m.get('key') == market_key:
                                for outc in m.get('outcomes', []):
                                    if outc.get('name') == name:
                                        all_odds.append(outc.get('price'))
                    if not all_odds:
                        continue
                    avg_odd = sum(all_odds) / len(all_odds)

                    # Стойностен залог, ако коефициентът на букмейкъра е поне 10% по-висок от средния
                    if odd > avg_odd * 1.1:
                        value_bets.append({
                            "teams": teams,
                            "time": commence_time,
                            "league": league,
                            "bookmaker": bookmaker.get('title'),
                            "bet": f"{market_key} - {name}",
                            "odd": odd,
                            "avg_odd": round(avg_odd, 2)
                        })
    return value_bets

def main():
    st.title("Стойностни Залози - Автоматичен Анализ")
    st.write("Цел: Да показва само най-стойностните залози за деня - автоматично подбрани.")

    st.write("Зареждам мачове от основните европейски първенства...")

    all_value_bets = []
    for league in EUROPE_LEAGUES:
        odds_data = fetch_odds(league)
        if odds_data:
            value_bets = calculate_value_bets(odds_data)
            all_value_bets.extend(value_bets)

    if not all_value_bets:
        st.info("Няма открити стойностни залози за днес.")
    else:
        st.success(f"Намерени {len(all_value_bets)} стойностни залози:")
        for bet in all_value_bets:
            teams = bet.get('teams')
            if teams and isinstance(teams, list) and len(teams) == 2:
                match_str = f"**{teams[0]} vs {teams[1]}**"
            else:
                match_str = "Неизвестен мач"

            time_str = bet.get('time', 'Неизвестно време')
            league = bet.get('league', 'Неизвестна лига')
            bookmaker = bet.get('bookmaker', 'Неизвестен букмейкър')
            bet_name = bet.get('bet', 'Неизвестен залог')
            odd = bet.get('odd', '?')
            avg_odd = bet.get('avg_odd', '?')

            st.write(f"{match_str} ({time_str})")
            st.write(f"Лига: {league}")
            st.write(f"Букмейкър: {bookmaker}")
            st.write(f"Залог: {bet_name}")
            st.write(f"Коефициент: {odd} (Среден коефициент: {avg_odd})")
            st.write("---")

if __name__ == "__main__":
    main()
