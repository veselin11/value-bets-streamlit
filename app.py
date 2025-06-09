import requests
from datetime import datetime

ODDS_API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

def get_all_sports():
    url = "https://api.the-odds-api.com/v4/sports"
    params = {
        "apiKey": ODDS_API_KEY
    }
    res = requests.get(url, params=params)
    return res.json()

def get_odds_for_football_leagues():
    sports = get_all_sports()
    football_sports = [s for s in sports if "soccer" in s["key"] and s["active"]]

    print(f"Намерени {len(football_sports)} активни футболни лиги.\n")

    for sport in football_sports:
        print(f"Проверяваме: {sport['title']} ({sport['key']})")
        url = f"https://api.the-odds-api.com/v4/sports/{sport['key']}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            print(f" ❌ Грешка за {sport['key']}")
            continue

        data = res.json()
        if not data:
            print(" ⚠️  Няма налични мачове.\n")
            continue

        print(f" ✅ {len(data)} мача намерени.\n")
        for match in data[:3]:  # само първите 3
            print(f"- {match['home_team']} vs {match['away_team']}")
            print(f"  Начало: {match['commence_time']}")
            for book in match['bookmakers'][:1]:
                for market in book['markets']:
                    if market['key'] == 'h2h':
                        print("  Коефициенти:")
                        for outcome in market['outcomes']:
                            print(f"   - {outcome['name']}: {outcome['price']}")
            print()

get_odds_for_football_leagues()
