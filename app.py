import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone

# Конфигурация
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("Липсва API ключ")
    st.stop()

# Настройки
TIMEZONE = timezone("Europe/Sofia")
SPORTS = ["soccer_epl", "soccer_laliga", "soccer_bundesliga", "soccer_serie_a", "soccer_ligue1"]

# Функции за данни
@st.cache_data(ttl=3600)
def get_all_sports():
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY}
        )
        return {sport["key"]: sport["title"] for sport in response.json()}
    except Exception as e:
        st.error(f"Грешка при взимане на спортни лиги: {str(e)}")
        return {}

@st.cache_data(ttl=600)
def get_matches(sport_key, date_from, date_to):
    try:
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "eu",
                "dateFormat": "iso",
                "markets": "h2h",
                "commenceTimeFrom": date_from,
                "commenceTimeTo": date_to
            }
        )
        return response.json()
    except Exception as e:
        st.error(f"Грешка при взимане на мачове: {str(e)}")
        return []

# Интерфейс
def main():
    st.set_page_config(page_title="Мачове - Днес & Утре", layout="wide")
    st.title("⚽ Всички мачове - Днес и Утре")
    
    # Времеви диапазон
    now = datetime.now(TIMEZONE)
    date_from = now.replace(hour=0, minute=0, second=0).isoformat()
    date_to = (now + timedelta(days=2)).replace(hour=23, minute=59, second=59).isoformat()
    
    # Зареди всички спортни лиги
    sports = get_all_sports()
    
    # Филтър за дати
    today = now.date()
    tomorrow = today + timedelta(days=1)
    
    # Зареди всички мачове
    all_matches = []
    for sport_key in SPORTS:
        matches = get_matches(sport_key, date_from, date_to)
        for match in matches:
            match_time = datetime.fromisoformat(match["commence_time"]).astimezone(TIMEZONE)
            all_matches.append({
                "Лига": sports.get(sport_key, sport_key),
                "Домакин": match["home_team"],
                "Гост": match["away_team"],
                "Дата": match_time.strftime("%d.%m"),
                "Час": match_time.strftime("%H:%M"),
                "Ден": "Днес" if match_time.date() == today else "Утре",
                "Bookmakers": len(match["bookmakers"])
            })
    
    # Създай DataFrame
    df = pd.DataFrame(all_matches).sort_values(["Дата", "Час"])
    
    # Покажи мачове
    st.header(f"Общо мачове: {len(df)}")
    
    # Групирай по ден и лига
    for day_group in ["Днес", "Утре"]:
        day_df = df[df["Ден"] == day_group]
        if not day_df.empty:
            st.subheader(day_group)
            
            for league in day_df["Лига"].unique():
                league_df = day_df[day_df["Лига"] == league]
                with st.expander(f"{league} ({len(league_df)} мача)"):
                    st.dataframe(
                        league_df[["Домакин", "Гост", "Час", "Bookmakers"]],
                        column_config={
                            "Bookmakers": st.column_config.NumberColumn(
                                "Букмейкъри",
                                help="Брой предлагащи букмейкъри"
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )

if __name__ == "__main__":
    main()
