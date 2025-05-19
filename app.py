import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pytz import timezone
import logging

# Конфигурация
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("❌ Липсва API ключ в secrets.toml")
    st.stop()

# Настройки
LOCAL_TZ = timezone("Europe/Sofia")

# Настройки на логирането
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_all_soccer_leagues():
    """Вземи всички футболни лиги с нова филтрация"""
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY},
            timeout=15
        )
        
        if response.status_code != 200:
            logger.error(f"API Грешка: {response.status_code}")
            return []
            
        return [
            league["key"] 
            for league in response.json()
            if league["sport_key"].startswith("soccer") 
            and league["active"] is True
        ]
        
    except Exception as e:
        logger.error(f"Грешка при взимане на лиги: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Global Bets Solution", layout="wide")
    st.title("⚽ Value Bets - Работещо Решение")
    
    # Зареди лиги
    leagues = get_all_soccer_leagues()
    
    if not leagues:
        st.error("Не са намерени активни футболни лиги")
        return
    
    st.success(f"Намерени {len(leagues)} лиги")
    
    # Покажи първи 10 мача от първата лига за демонстрация
    if st.button("Покажи примерни мачове"):
        try:
            matches = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{leagues[0]}/odds",
                params={
                    "apiKey": ODDS_API_KEY,
                    "regions": "eu",
                    "markets": "h2h"
                },
                timeout=15
            ).json()
            
            st.subheader(f"Примерни мачове от {leagues[0]}:")
            for match in matches[:5]:
                commence_time = datetime.fromisoformat(match["commence_time"]).astimezone(LOCAL_TZ)
                st.write(f"""
                    - {match["home_team"]} vs {match["away_team"]}
                    ⏰ {commence_time.strftime("%d.%m %H:%M")}
                    📊 {len(match["bookmakers"])} букмейкъра
                """)
                
        except Exception as e:
            st.error(f"Грешка при взимане на мачове: {str(e)}")

if __name__ == "__main__":
    main()
