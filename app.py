import streamlit as st
import requests
from datetime import datetime

API_KEY = "ТВОЯ_API_KEY"
API_HOST = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}

def get_today_matches():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{API_HOST}/fixtures?date={today}"

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        matches = []
        for fixture in data.get("response", []):
            home = fixture["teams"]["home"]["name"]
            away = fixture["teams"]["away"]["name"]
            fixture_id = fixture["fixture"]["id"]

            matches.append({
                "home_team": home,
                "away_team": away,
                "fixture_id": fixture_id
            })

        return matches
    except Exception as e:
        print(f"[ERROR] Грешка при зареждане на мачовете: {e}")
        return []

def get_team_stats(team_name):
    url = f"{API_HOST}/teams?search={team_name}"

    try:
        res = requests.get(url, headers=headers)
        teams = res.json().get("response", [])

        if not teams:
            return []

        team_id = teams[0]["team"]["id"]

        # Взимаме последните 10 мача (играни)
        matches_url = f"{API_HOST}/fixtures?team={team_id}&status=FT&last=10"
        res2 = requests.get(matches_url, headers=headers)
        match_data = res2.json().get("response", [])

        stats = []
        for match in match_data:
            is_home = match["teams"]["home"]["id"] == team_id
            goals_scored = match["goals"]["home"] if is_home else match["goals"]["away"]

            stats.append({
                "opponent": match["teams"]["away"]["name"] if is_home else match["teams"]["home"]["name"],
                "goals_scored": goals_scored,
                "is_home": is_home
            })

        return stats
    except Exception as e:
        print(f"[ERROR] Грешка при зареждане на статистика за {team_name}: {e}")
        return []

def main():
    st.title("Value Bets Finder")
    st.write("Зареждане на мачове и статистика за днешния ден...")

    matches = get_today_matches()

    if not matches:
        st.warning("Няма намерени мачове за днес.")
        return

    for match in matches:
        home_stats = get_team_stats(match["home_team"])
        away_stats = get_team_stats(match["away_team"])

        st.subheader(f"{match['home_team']} vs {match['away_team']}")
        st.write("**Последни 10 мача на домакините:**")
        st.write(home_stats)
        st.write("**Последни 10 мача на гостите:**")
        st.write(away_stats)

if __name__ == "__main__":
    main()
    
