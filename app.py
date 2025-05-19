import streamlit as st
import requests

# Конфигурация
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("❌ Липсва API ключ в secrets.toml")
    st.stop()

def get_active_soccer_leagues():
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
            if league.get("sport_key") == "soccer"  # Филтрирай само главния футболен раздел
            and league.get("active")
            and "football" in league.get("title", "").lower()  # Допълнителна проверка за футбол
        ]
        
        return soccer_leagues
        
    except Exception as e:
        st.error(f"Грешка при връзка: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Футболни Лиги", layout="wide")
    st.title("⚽ Футболни Лиги - Работещо Решение")
    
    # Тест на API ключ
    with st.expander("🔍 Тест на API ключ"):
        test_response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY}
        )
        if test_response.status_code == 200:
            st.success("✅ API ключ работи успешно!")
        else:
            st.error(f"❌ Грешка {test_response.status_code}: {test_response.text}")
    
    # Вземи лиги
    leagues = get_active_soccer_leagues()
    
    if not leagues:
        st.error("""
            🚨 Няма намерени футболни лиги. Възможни причини:
            1. Няма активни мачове в момента
            2. Ключът няма права за футболни лиги
            3. Проблем с API сървъра
            """)
        return
    
    st.success(f"Намерени {len(leagues)} активни футболни лиги:")
    for league in leagues:
        st.write(f"- {league}")

if __name__ == "__main__":
    main()
