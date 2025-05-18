import streamlit as st
import requests
import datetime

# Заглавие
st.title("Стойностни Залози - Автоматичен Анализ")
st.caption("Цел: Да показва само най-стойностните залози за деня - автоматично подбрани.")

# Въведете вашия API ключ тук
API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

# Дефиниране на целевите пазари и региони
REGIONS = "eu"
MARKETS = ["h2h", "totals", "both_teams_to_score"]  # 1X2, Over/Under, GG/NG
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"

# Европейски лиги, които ще проверяваме
LEAGUES = [
    "soccer_epl",  # Англия
    "soccer_uefa_champs_league",
    "soccer_uefa_europa_league",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_spain_la_liga",
    "soccer_france_ligue_one",
    "soccer_netherlands_eredivisie",
    "soccer_greece_super_league",
    "soccer_portugal_primeira_liga",
    "soccer_romania_liga_1",
    "soccer_bulgaria_first_league"
]

# Функция за извличане на мачове
@st.cache_data(ttl=3600)
def load_matches(league):
    url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={','.join(MARKETS)}&oddsFormat={ODDS_FORMAT}&dateFormat={DATE_FORMAT}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Грешка при зареждане на {league}: {e}")
        return []

# Функция за избор на стойностни залози
def is_value_bet(odds_list, fair_odds_threshold=0.95):
    # Проста проверка: дали някой от коефициентите е значително по-висок от останалите (примерна логика)
    if not odds_list or len(odds_list) < 3:
        return []

    values = []
    avg_odds = {}

    for outcome in ["home", "away", "draw"]:
        outcome_odds = [bookmaker['outcomes'] for bookmaker in odds_list if 'outcomes' in bookmaker]
        flat = [out for sublist in outcome_odds for out in sublist if out['name'].lower() == outcome]
        if not flat:
            continue
        avg = sum([float(x['price']) for x in flat]) / len(flat)
        best = max([float(x['price']) for x in flat])
        if best > avg * 1.1:  # 10% стойностен праг
            values.append((outcome, best))

    return values

# Анализ и показване
def analyze_and_display():
    value_bets = []

    st.subheader("Зареждам мачове от всички основни европейски първенства...")

    for league in LEAGUES:
        matches = load_matches(league)

        for match in matches:
            if 'teams' not in match or not match['teams'] or len(match['teams']) < 2:
                continue

            home_team, away_team = match['teams'][0], match['teams'][1]
            commence_time = match['commence_time']
            bookmakers = match.get('bookmakers', [])

            for bookmaker in bookmakers:
                market = bookmaker.get('markets', [])
                for m in market:
                    if m['key'] == 'h2h':
                        val = is_value_bet([m])
                        for outcome, odd in val:
                            value_bets.append({
                                "match": f"{home_team} vs {away_team}",
                                "league": league,
                                "bookmaker": bookmaker['title'],
                                "outcome": outcome,
                                "odd": odd,
                                "start": commence_time
                            })

    if value_bets:
        st.subheader("Намерени стойностни залози:")
        for vb in sorted(value_bets, key=lambda x: x['start']):
            st.markdown(f"**{vb['match']}** ({vb['start']})")
            st.write(f"Лига: {vb['league']}")
            st.write(f"Букмейкър: {vb['bookmaker']}")
            st.write(f"Залог: {vb['outcome'].capitalize()}")
            st.write(f"Коефициент: {vb['odd']}")
            st.markdown("---")
    else:
        st.info("Няма открити стойностни залози за днес.")

# Стартиране на анализа
analyze_and_display()
