import streamlit as st
import requests
import pandas as pd

# Конфигурация
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("❌ Липсва API ключ в secrets.toml")
    st.stop()

def get_active_leagues():
    """Вземи активни футболни лиги с нова филтрация"""
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY},
            timeout=15
        )
        
        if response.status_code != 200:
            st.error(f"API Грешка {response.status_code}: {response.text}")
            return []
            
        leagues = response.json()
        soccer_leagues = [
            league["key"] 
            for league in leagues 
            if league["sport_key"] == "soccer" 
            and league["active"] 
            and "match" in league["description"].lower()
        ]
        
        return soccer_leagues
        
    except Exception as e:
        st.error(f"Грешка при връзка: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Работещо Решение", layout="wide")
    st.title("✅ Демо на Работещо Решение")
    
    # Ръчен тестер на API
    with st.expander("🔍 Тест на API ключ"):
        if st.button("Тествай връзка с API"):
            test_response = requests.get(
                "https://api.the-odds-api.com/v4/sports",
                params={"apiKey": ODDS_API_KEY}
            )
            if test_response.status_code == 200:
                st.success("API ключ работи успешно!")
                st.json(test_response.json()[:1])  # Покажи първата лига
            else:
                st.error(f"Грешка {test_response.status_code}: {test_response.text}")
    
    # Вземи лиги
    leagues = get_active_leagues()
    
    if not leagues:
        st.error("""
            Няма намерени лиги. Възможни причини:
            1. Невалиден API ключ
            2. Няма активни мачове в момента
            3. Проблем с API сървъра
            """)
        return
    
    st.success(f"Намерени {len(leagues)} активни лиги")
    st.write("Примерни лиги:", leagues[:5])  # Покажи първите 5 лиги

if __name__ == "__main__":
    main()
