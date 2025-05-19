import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from pytz import timezone as tz

# Конфигурация
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("❌ Липсва API ключ в secrets.toml")
    st.stop()

# Настройки
LOCAL_TZ = tz("Europe/Sofia")
SPORTS = {
    "soccer_epl": "Англия - Висша Лига",
    "soccer_spain_la_liga": "Испания - Ла Лига",
    "soccer_germany_bundesliga": "Германия - Бундеслига",
    "soccer_italy_serie_a": "Италия - Серия А",
    "soccer_france_ligue_one": "Франция - Лига 1"
}
DAYS_AHEAD = 3

def get_utc_iso(time: datetime) -> str:
    """Конвертира време към UTC ISO формат"""
    return time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

@st.cache_data(ttl=600)
def get_matches(sport_key: str):
    """Вземи мачове от API"""
    try:
        now = datetime.now(timezone.utc)
        date_from = get_utc_iso(now)
        date_to = get_utc_iso(now + timedelta(days=DAYS_AHEAD))

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

        if response.status_code == 401:
            st.error("⛔ Невалиден API ключ")
            return []
        if response.status_code != 200:
            return []

        return response.json()
    except Exception as e:
        st.error(f"🚨 Грешка при връзка: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="⚽ Live Matches", layout="wide")
    st.title("🔴 Live Мачове Трекер")
    
    all_matches = []
    
    for sport_key, sport_name in SPORTS.items():
        with st.spinner(f"Зареждане на {sport_name}..."):
            matches = get_matches(sport_key)
            
            for match in matches:
                try:
                    match_time = datetime.fromisoformat(match["commence_time"]).astimezone(LOCAL_TZ)
                    if match_time < datetime.now(LOCAL_TZ):
                        continue
                        
                    all_matches.append({
                        "Лига": sport_name,
                        "Домакин": match["home_team"],
                        "Гост": match["away_team"],
                        "Дата": match_time.strftime("%d.%m"),
                        "Час": match_time.strftime("%H:%M"),
                        "Букмейкъри": len(match["bookmakers"])
                    })
                except KeyError:
                    continue

    if not all_matches:
        st.warning("""
            🏟️ Няма намерени мачове. Възможни причини:
            1. Няма предстоящи мачове в следващите 3 дни
            2. Изчерпани са API заявките
            3. Проблем с интернет връзката
            """)
        return

    # Сортирай и покажи данните
    df = pd.DataFrame(all_matches).sort_values(["Дата", "Час"])
    
    st.subheader(f"🔍 Намерени мачове: {len(df)}")
    st.dataframe(
        df,
        column_config={
            "Букмейкъри": st.column_config.NumberColumn(
                format="%d 🏦",
                help="Брой предлагащи букмейкъри"
            )
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

if __name__ == "__main__":
    main()
