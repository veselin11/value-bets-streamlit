import requests

API_KEY = '2e086a4b6d758dec878ee7b5593405b1'
BASE_URL = 'https://api.the-odds-api.com/v4'

sport_key = 'soccer_epl'
markets = ['h2h', 'totals', 'both_teams_to_score']
regions = 'eu'
odds_format = 'decimal'
date_format = 'iso'

url = f"{BASE_URL}/sports/{sport_key}/odds"
params = {
    'apiKey': API_KEY,
    'regions': regions,
    'markets': ','.join(markets),
    'oddsFormat': odds_format,
    'dateFormat': date_format
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    # Обработка на данните
else:
    print(f"Грешка: {response.status_code} - {response.text}")
