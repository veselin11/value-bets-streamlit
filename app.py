import requests

API_KEY = "YOUR_API_KEY"
SPORT_KEY = "soccer_epl"
REGION = "eu"
MARKET = "h2h"
ODDS_FORMAT = "decimal"

url = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds"
params = {
    "apiKey": API_KEY,
    "regions": REGION,
    "markets": MARKET,
    "oddsFormat": ODDS_FORMAT
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Грешка: {response.status_code}")
    print(response.text)
