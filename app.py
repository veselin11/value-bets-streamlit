import requests

API_KEY = "4474e2c1f44b1561daf6c481deb050cb"
API_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds/"

params = {
    "apiKey": API_KEY,
    "regions": "eu",
    "markets": "h2h",
    "oddsFormat": "decimal",
    "dateFormat": "iso"
}

response = requests.get(API_URL, params=params)

if response.status_code == 200:
    print("Успешна връзка с API.")
    data = response.json()
    print(data)
else:
    print(f"Грешка при връзка с API: {response.status_code} - {response.text}")
