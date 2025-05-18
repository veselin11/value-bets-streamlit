import streamlit as st
import requests

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

# Лиги, които да проверяваме (само валидни за The Odds API)
LEAGUES = [
    "soccer_epl",               # Англия - Премиър Лийг
    "soccer_spain_la_liga",     # Испания - Ла Лига
    "soccer_germany_bundesliga",# Германия - Бундеслига
    "soccer_italy_serie_a",     # Италия - Серия А
    "soccer_france_ligue_one",  # Франция - Лига 1
    "soccer_netherlands_eredivisie",
    "soccer_portugal_liga",
    "soccer_russia_premier_league",
    "soccer_turkey_superlig"
]

def get_odds_for_league(league):
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",  # Само 1X2
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.warning(f"Грешка при зареждане на {league}: {e}")
    except Exception as e:
        st.warning(f"Грешка при заявката за {league}: {e}")
    return None

def find_value_bets(matches):
    value_bets = []
    if not matches:
        return value_bets
    for match in matches:
        teams = match.get("teams")
        commence_time = match.get("commence_time")
        bookmakers = match.get("bookmakers", [])
        # Намираме средния коефициент за всеки изход от всички букмейкъри
        outcomes_sum = {}
        outcomes_count = {}
        for bm in bookmakers:
            for market in bm.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price")
                    if name and price:
                        outcomes_sum[name] = outcomes_sum.get(name, 0) + price
                        outcomes_count[name] = outcomes_count.get(name, 0) + 1
        # Средни коефициенти
        avg_odds = {k: outcomes_sum[k]/outcomes_count[k] for k in outcomes_sum}

        # Текущите коефициенти на букмейкъра Pinnacle (ако има)
        pinnacle = next((bm for bm in bookmakers if bm.get("title","").lower() == "pinnacle"), None)
        if pinnacle:
            pinnacle_market = next((m for m in pinnacle.get("markets", []) if m.get("key") == "h2h"), None)
            if pinnacle_market:
                for outcome in pinnacle_market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price")
                    if name and price and name in avg_odds:
                        # Проверяваме дали коефициентът е стойностен (по-голям от средния)
                        if price > avg_odds[name]:
                            value_bets.append({
                                "teams": teams,
                                "time": commence_time,
                                "league": match.get("sport_key"),
                                "bookmaker": pinnacle.get("title"),
                                "bet": name,
                                "odd": price,
                                "avg_odd": round(avg_odds[name], 2)
                            })
    return value_bets

def main():
    st.title("Стойностни Залози - Автоматичен Анализ")
    st.write("Цел: Да показва само най-стойностните залози за деня - автоматично подбрани.")

    st.write("Зареждам мачове от основните европейски първенства...")

    all_value_bets = []

    for league in LEAGUES:
        matches = get_odds_for_league(league)
        if matches:
            league_value_bets = find_value_bets(matches)
            if league_value_bets:
                all_value_bets.extend(league_value_bets)

    if not all_value_bets:
        st.info("Няма открити стойностни залози за днес.")
    else:
        st.success(f"Намерени {len(all_value_bets)} стойностни залози:")
        for bet in all_value_bets:
            st.write(f"**{bet['teams'][0]} vs {bet['teams'][1]}** ({bet['time']})")
            st.write(f"Лига: {bet['league']}")
            st.write(f"Букмейкър: {bet['bookmaker']}")
            st.write(f"Залог: {bet['bet']}")
            st.write(f"Коефициент: {bet['odd']} (Среден коефициент: {bet['avg_odd']})")
            st.write("---")

if __name__ == "__main__":
    main()
