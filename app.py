import requests

API_KEY = '2e086a4b6d758dec878ee7b5593405b1'
BASE_URL = 'https://api.the-odds-api.com/v4'

# Лиги, които искаш да следиш
leagues = [
    'soccer_epl',               # Англия - Висша лига
    'soccer_spain_la_liga',     # Испания - Ла Лига
    'soccer_germany_bundesliga',# Германия - Бундеслига
    'soccer_italy_serie_a',     # Италия - Серия А
    'soccer_france_ligue_one',  # Франция - Лига 1
    'soccer_netherlands_eredivisie', # Холандия
    'soccer_portugal_liga'      # Португалия
]

def get_valid_markets(sport_key):
    url = f"{BASE_URL}/sports/{sport_key}/markets"
    params = {'apiKey': API_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        markets = resp.json()
        print(f"[INFO] Лига {sport_key} - валидни пазари: {markets}")
        return markets
    else:
        print(f"[ERROR] Неуспешно зареждане пазари за {sport_key}: {resp.status_code} {resp.text}")
        return []

def get_odds(sport_key, markets):
    url = f"{BASE_URL}/sports/{sport_key}/odds"
    params = {
        'apiKey': API_KEY,
        'regions': 'eu',
        'markets': ','.join(markets),
        'oddsFormat': 'decimal',
        'dateFormat': 'iso'
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"[ERROR] Неуспешно зареждане коефициенти за {sport_key}: {resp.status_code} {resp.text}")
        return []

def main():
    for league in leagues:
        valid_markets = get_valid_markets(league)
        if not valid_markets:
            continue
        
        odds_data = get_odds(league, valid_markets)
        if not odds_data:
            continue
        
        print(f"\n--- {league} ---")
        for match in odds_data:
            teams = match.get('teams', ['N/A', 'N/A'])
            commence_time = match.get('commence_time', 'N/A')
            print(f"Мач: {teams[0]} vs {teams[1]} | Начален час: {commence_time}")
            
            for bookmaker in match.get('bookmakers', []):
                print(f"  Букмейкър: {bookmaker.get('title', 'N/A')}")
                for market in bookmaker.get('markets', []):
                    market_key = market.get('key', '')
                    outcomes = market.get('outcomes', [])
                    print(f"    Пазар: {market_key}")
                    for outcome in outcomes:
                        print(f"      {outcome.get('name', 'N/A')}: {outcome.get('price', 'N/A')}")
            print()

if __name__ == "__main__":
    main()
