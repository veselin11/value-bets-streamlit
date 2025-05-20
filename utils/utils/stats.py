# utils/stats.py

import requests

TEAM_ID_MAPPING = {
    "Liverpool": 64,
    "Manchester City": 65,
    "Arsenal": 57,
    "Slavia Sofia": 7325,
    "Ludogorets": 7391,
    # добави още според нуждите
}

API_FOOTBALL_TOKEN = "YOUR_API_TOKEN"

def fetch_team_stats(team_name):
    if team_name not in TEAM_ID_MAPPING:
        return None
    team_id = TEAM_ID_MAPPING[team_name]
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
    headers = {"X-Auth-Token": API_FOOTBALL_TOKEN}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None

    data = response.json()
    matches = data.get("matches", [])
    return [f"{m['homeTeam']['name']} {m['score']['fullTime']['home']}:{m['score']['fullTime']['away']} {m['awayTeam']['name']}" for m in matches]
