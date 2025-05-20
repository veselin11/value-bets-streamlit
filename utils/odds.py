# utils/odds.py

import requests
import os

API_KEY = os.getenv("ODDS_API_KEY") or "2e086a4b6d758dec878ee7b5593405b1"
REGION = "eu"
MARKETS = ["h2h", "over_under", "both_teams_to_score"]
BOOKMAKER = "pinnacle"

def fetch_value_bets():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={API_KEY}&regions={REGION}&markets={','.join(MARKETS)}&oddsFormat=decimal"
    response = requests.get(url)

    if response.status_code != 200:
        return []

    games = response.json()
    value_bets = []

    for game in games:
        if "bookmakers" not in game:
            continue
        for bookmaker in game["bookmakers"]:
            for market in bookmaker["markets"]:
                for outcome in market["outcomes"]:
                    if outcome["price"] > 2.0:  # Просто примерно value условие
                        value_bets.append({
                            "match": game,
                            "market": market["key"],
                            "outcome": outcome["name"],
                            "odds": outcome["price"],
                            "bookmaker": bookmaker["title"],
                            "value": 0.15  # фиктивна стойност, за тест
                        })

    return value_bets
