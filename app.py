import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
import iso8601
from typing import Optional

# Конфигурация
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("Липсва API ключ")
    st.stop()

# Настройки
LOCAL_TZ = timezone("Europe/Sofia")
SPORTS = ["soccer_epl", "soccer_laliga", "soccer_bundesliga", "soccer_serie_a", "soccer_ligue1"]
DAYS_AHEAD = 3  # Вземи мачове за следващите 3 дни

def parse_iso_time(time_str: str) -> Optional[datetime]:
    """Парсване на ISO време със защита от грешки"""
    try:
        dt = iso8601.parse_date(time_str)
        return dt.astimezone(LOCAL_TZ)
    except Exception as e:
        st.error(f"Грешка при парсване на време: {str(e)}")
        return None

@st.cache_data(ttl=600)
def get_matches(sport_key: str):
    """Вземи мачове за следващите DAYS_AHEAD дни"""
    try:
        now_utc = datetime.utcnow().replace(tzinfo=timezone("UTC"))
        date_from = now_utc.isoformat()
        date_to = (now_utc + timedelta(days=DAYS_AHEAD)).isoformat()

        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "markets": "h2h",
                "commenceTimeFrom": date_from,
                "commenceTimeTo": date_to
            },
            timeout=15
        )
        
        if response.status_code != 200:
            st.error(f"API грешка: {response.status_code} - {response.text}")
            return []

        return response.json()
    except Exception as e:
        st.error(f"Грешка при заявка: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Мачове", layout="wide")
    st.title("⚽ Програма за мачове")
    
    all_matches = []
    
    # Вземи мачове за всички лиги
    for sport_key in SPORTS:
        matches = get_matches(sport_key)
        
        for match in matches:
            match_time = parse_iso_time(match.get("commence_time", ""))
            if not match_time:
                continue
                
            time_diff = match_time - datetime.now(LOCAL_TZ)
            if time_diff < timedelta(0):
                continue  # Пропусни минали мачове
                
            all_matches.append({
                "Лига": sport_key.replace("soccer_", "").upper(),
                "Домакин": match.get("home_team", "?"),
                "Гост": match.get("away_team", "?"),
                "Дата": match_time.strftime("%d.%m.%Y"),
                "Час": match_time.strftime("%H:%M"),
                "До мача": f"{time_diff.total_seconds()//3600:.0f}ч",
                "Букмейкъри": len(match.get("bookmakers", []))
            })

    if not all_matches:
        st.warning("""
            Няма намерени мачове. Възможни причини:
            1. Няма предстоящи мачове в избраните лиги
            2. Проблем с API ключа
            3. Ограничение на API заявките
            """)
        return

    # Покажи данните
    df = pd.DataFrame(all_matches).sort_values(["Дата", "Час"])
    
    st.subheader(f"Намерени мачове: {len(df)}")
    st.dataframe(
        df,
        column_config={
            "Букмейкъри": st.column_config.NumberColumn(
                format="%d ⚖️",
                help="Брой предлагащи букмейкъри"
            )
        },
        hide_index=True,
        use_container_width=True
    )

if __name__ == "__main__":
    main()
