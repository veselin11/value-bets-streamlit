import requests

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"
URL = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"

response = requests.get(URL)
sports = response.json()

for sport in sports:
    print(f"{sport['key']}: {sport['title']}")
