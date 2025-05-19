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
FALLBACK_LEAGUES = [
    "soccer_epl", "soccer_spain_la_liga", 
    "soccer_germany_bundesliga", "soccer_italy_serie_a"
]

# Настройки на логирането
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_api_response(response: requests.Response):
    """Дебъг информация за API отговори"""
    debug_info = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "first_100_chars": response.text[:100],
        "url": response.url
    }
    return debug_info

def get_all_soccer_leagues():
    """Вземи всички футболни лиги с подобрена филтрация"""
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY},
            timeout=15
        )
        
        logger.debug(f"API Debug: {debug_api_response(response)}")
        
        if response.status_code != 200:
            logger.error(f"API Грешка: {response.status_code} - {response.text}")
            return FALLBACK_LEAGUES
            
        all_leagues = response.json()
        soccer_leagues = []
        
        for league in all_leagues:
            # Разширена филтрация
            is_soccer = (
                "soccer" in league["key"].lower() or 
                "football" in league["title"].lower()
            )
            has_odds = league["active"]
            is_match_based = any(word in league["description"].lower() 
                             for word in ["match", "game", "fixture"])
            
            if is_soccer and has_odds and is_match_based:
                soccer_leagues.append({
                    "key": league["key"],
                    "title": league["title"],
                    "active": league["active"],
                    "details": league["description"]
                })
        
        if not soccer_leagues:
            logger.warning("Фалбек към предварителни лиги")
            return FALLBACK_LEAGUES
            
        return [league["key"] for league in soccer_leagues]
        
    except Exception as e:
        logger.error(f"Критична грешка: {str(e)}", exc_info=True)
        return FALLBACK_LEAGUES

def main():
    st.set_page_config(page_title="Global Bets Debug", layout="wide")
    st.title("🔍 Дебъг на Футболни Лиги")
    
    # Ръчно тестване на API
    with st.expander("🐞 Ръчен API Тестер"):
        test_key = st.text_input("Въведи API ключ за тест", type="password")
        if st.button("Тествай API"):
            try:
                test_response = requests.get(
                    "https://api.the-odds-api.com/v4/sports",
                    params={"apiKey": test_key or ODDS_API_KEY}
                )
                st.json(debug_api_response(test_response))
            except Exception as e:
                st.error(f"Тестова грешка: {str(e)}")
    
    # Автоматично зареждане
    st.subheader("Автоматично откриване на лиги")
    leagues = get_all_soccer_leagues()
    
    if not leagues:
        st.error("""
            🚨 Критичен проблем:
            1. Провери интернет връзка
            2. Провери API ключ
            3. Опитай с различен регион
            """)
        return
    
    st.success(f"Намерени лиги ({len(leagues)}):")
    for league in leagues:
        st.write(f"- {league}")
    
    # Допълнителна информация
    with st.expander("Технически детайли"):
        st.write("""
            **Логика на филтрация:**
            1. Ключ съдържа 'soccer'
            2. Активни лиги
            3. Описание съдържа 'match', 'game' или 'fixture'
            """)

if __name__ == "__main__":
    main()
