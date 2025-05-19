import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
import iso8601  # Трябва да инсталирате този пакет

# Конфигурация
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("Липсва API ключ")
    st.stop()

# Настройки
TIMEZONE = timezone("Europe/Sofia")
SPORTS = ["soccer_epl", "soccer_laliga", "soccer_bundesliga", "soccer_serie_a", "soccer_ligue1"]

def parse_iso_time(time_str):
    """Безопасен парсър за ISO време"""
    try:
        return iso8601.parse_date(time_str).astimezone(TIMEZONE)
    except (TypeError, ValueError, iso8601.ParseError) as e:
        st.warning(f"Грешка при парсване на време: {time_str} - {str(e)}")
        return None

@st.cache_data(ttl=600)
def get_matches(sport_key, date_from, date_to):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "commenceTimeFrom": date_from,
                "commenceTimeTo": date_to
            }
        )
        return response.json()
    except Exception as e:
        st.error(f"Грешка при взимане на мачове: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Мачове - Днес & Утре", layout="wide")
    st.title("⚽ Всички мачове - Днес и Утре")
    
    now = datetime.now(TIMEZONE)
    date_from = now.replace(hour=0, minute=0, second=0).isoformat()
    date_to = (now + timedelta(days=2)).replace(hour=23, minute=59, second=59).isoformat()
    
    all_matches = []
    for sport_key in SPORTS:
        matches = get_matches(sport_key, date_from, date_to)
        for match in matches:
            if "commence_time" not in match:
                continue
                
            match_time = parse_iso_time(match["commence_time"])
            if not match_time:
                continue
            
            all_matches.append({
                "Лига": sport_key.replace("soccer_", "").upper(),
                "Домакин": match.get("home_team", "N/A"),
                "Гост": match.get("away_team", "N/A"),
                "Дата": match_time.strftime("%d.%m"),
                "Час": match_time.strftime("%H:%M"),
                "Ден": "Днес" if match_time.date() == now.date() else "Утре",
                "Bookmakers": len(match.get("bookmakers", []))
            })

    if not all_matches:
        st.warning("Няма налични мачове за избрания период")
        return

    df = pd.DataFrame(all_matches).sort_values(["Дата", "Час"])
    
    # Останалата част на кода остава същата...

if __name__ == "__main__":
    main()
