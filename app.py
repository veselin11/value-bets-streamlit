import requests
from datetime import datetime

# Ключът за достъп до OddsAPI
API_KEY = "a3d6004cbbb4d16e86e2837c27e465d8"

# Текуща дата във формат YYYY-MM-DD
today = datetime.utcnow().strftime("%Y-%m-%d")

# Крайна точка на API за получаване на коефициенти
url = "https://api.the-odds-api.com/v4/sports/soccer/odds"

# Параметри на заявката
params = {
    "apiKey": API_KEY,
    "regions": "eu",  # Европейски букмейкъри
    "markets": "h2h",  # 1X2 пазар
    "oddsFormat": "decimal",
    "dateFormat": "iso",
    "date": today
}

# Изпращане на заявката
response = requests.get(url, params=params)
data = response.json()

# Примерна проверка за първия мач
first_game = data[0] if data else {}
first_game_info = {
    "teams": first_game.get("teams"),
    "commence_time": first_game.get("commence_time"),
    "bookmakers": first_game.get("bookmakers", [])
}

first_game_info
