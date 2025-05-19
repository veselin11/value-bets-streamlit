import streamlit as st
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from datetime import datetime, timedelta
from pytz import timezone
import logging

# Конфигурация
try:
    FD_API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except KeyError:
    st.error("❌ Липсват API ключове в secrets.toml")
    st.stop()

# Настройки
LOCAL_TZ = timezone("Europe/Sofia")
VALUE_THRESHOLD = 0.03  # Минимален праг за value bet (3%)
MAX_RETRIES = 3  # Максимални опити за API заявки

# Настройки на логирането
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_soccer_leagues():
    """Вземи всички футболни лиги от Odds API"""
    try:
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={"apiKey": ODDS_API_KEY}
        )
        leagues = response.json()
        return [
            league["key"] for league in leagues 
            if league["sport"].lower() == "soccer" 
            and "match" in league["description"].lower()
        ]
    except Exception as e:
        logger.error(f"Грешка при взимане на лиги: {str(e)}")
        return []

def get_team_id(team_name: str) -> int:
    """Връща ID на отбор с автоматично търсене"""
    for _ in range(MAX_RETRIES):
        try:
            response = requests.get(
                "https://api.football-data.org/v4/teams",
                headers={"X-Auth-Token": FD_API_KEY},
                params={"name": team_name},
                timeout=10
            )
            if response.status_code == 200 and response.json()["teams"]:
                return response.json()["teams"][0]["id"]
            return None
        except Exception as e:
            logger.warning(f"Ретиране на заявка за {team_name}")
    return None

@st.cache_data(ttl=3600)
def get_team_stats(team_id: int):
    """Вземи статистики за отбор"""
    try:
        response = requests.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": FD_API_KEY},
            params={"status": "FINISHED", "limit": 30},
            timeout=15
        )
        matches = response.json().get("matches", [])
        
        if not matches:
            return None
            
        home_goals = []
        away_goals = []
        results = []
        
        for match in matches[-15:]:  # Последни 15 мача
            if match["homeTeam"]["id"] == team_id:
                home_goals.append(match["score"]["fullTime"]["home"])
                results.append(1 if match["score"]["fullTime"]["home"] > match["score"]["fullTime"]["away"] else 0)
            else:
                away_goals.append(match["score"]["fullTime"]["away"])
                results.append(1 if match["score"]["fullTime"]["away"] > match["score"]["fullTime"]["home"] else 0)
        
        return {
            "avg_home": np.mean(home_goals) if home_goals else 1.2,
            "avg_away": np.mean(away_goals) if away_goals else 0.9,
            "form": results[-5:]  # Последни 5 мача
        }
    except Exception as e:
        logger.error(f"Грешка при взимане на статистики: {str(e)}")
        return None

def calculate_value_bet(match_data: dict):
    """Основна логика за изчисляване на value bet"""
    try:
        home_team = match_data["home_team"]
        away_team = match_data["away_team"]
        commence_time = datetime.fromisoformat(match_data["commence_time"]).astimezone(LOCAL_TZ)
        
        if commence_time < datetime.now(LOCAL_TZ):
            return None
            
        # Вземи ID на отбори
        home_id = get_team_id(home_team)
        away_id = get_team_id(away_team)
        
        if not home_id or not away_id:
            return None
            
        # Вземи статистики
        home_stats = get_team_stats(home_id)
        away_stats = get_team_stats(away_id)
        
        if not home_stats or not away_stats:
            return None
        
        # Изчисли вероятности
        home_avg = home_stats["avg_home"]
        away_avg = away_stats["avg_away"]
        
        home_prob, draw_prob, away_prob = 0.0, 0.0, 0.0
        for i in range(6):
            for j in range(6):
                p = poisson.pmf(i, home_avg) * poisson.pmf(j, away_avg)
                home_prob += p if i > j else 0
                draw_prob += p if i == j else 0
                away_prob += p if i < j else 0
        
        # Намери най-добри коефициенти
        bookmakers = match_data.get("bookmakers", [])
        if not bookmakers:
            return None
            
        home_odds = []
        draw_odds = []
        away_odds = []
        
        for bookmaker in bookmakers:
            for outcome in bookmaker["markets"][0]["outcomes"]:
                if outcome["name"] == home_team:
                    home_odds.append(outcome["price"])
                elif outcome["name"] == "Draw":
                    draw_odds.append(outcome["price"])
                elif outcome["name"] == away_team:
                    away_odds.append(outcome["price"])
        
        if not home_odds or not draw_odds or not away_odds:
            return None
            
        best_home = max(home_odds)
        best_draw = max(draw_odds)
        best_away = max(away_odds)
        
        # Имплицитни вероятности
        implied_home = 1 / best_home
        implied_draw = 1 / best_draw
        implied_away = 1 / best_away
        
        # Value изчисления
        value_home = home_prob - implied_home
        value_draw = draw_prob - implied_draw
        value_away = away_prob - implied_away
        
        if max(value_home, value_draw, value_away) < VALUE_THRESHOLD:
            return None
            
        return {
            "Лига": match_data["sport_title"],
            "Мач": f"{home_team} vs {away_team}",
            "Дата": commence_time.strftime("%d.%m %H:%M"),
            "Шанс Домакин": f"{home_prob*100:.1f}%",
            "Шанс Равен": f"{draw_prob*100:.1f}%",
            "Шанс Гост": f"{away_prob*100:.1f}%",
            "Value Домакин": value_home,
            "Value Равен": value_draw,
            "Value Гост": value_away,
            "Коеф. Домакин": best_home,
            "Коеф. Равен": best_draw,
            "Коеф. Гост": best_away,
            "Форма Домакин": "".join(["✅" if x == 1 else "❌" for x in home_stats["form"]]),
            "Форма Гост": "".join(["✅" if x == 1 else "❌" for x in away_stats["form"]])
        }
    except Exception as e:
        logger.error(f"Грешка при анализ на {home_team} vs {away_team}: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="🌍 Global Value Bets", layout="wide")
    st.title("⚽ Value Bets - Всички Лиги")
    
    try:
        # Вземи всички лиги
        leagues = get_all_soccer_leagues()
        if not leagues:
            st.error("Не са намерени футболни лиги")
            return
            
        # Прогрес бар
        progress_bar = st.progress(0)
        total_leagues = len(leagues)
        
        # Събиране на данни
        all_matches = []
        for idx, league in enumerate(leagues):
            try:
                # Зареди мачове за лигата
                response = requests.get(
                    f"https://api.the-odds-api.com/v4/sports/{league}/odds",
                    params={
                        "apiKey": ODDS_API_KEY,
                        "regions": "eu",
                        "markets": "h2h"
                    },
                    timeout=15
                )
                
                if response.status_code != 200:
                    continue
                    
                matches = response.json()
                for match in matches:
                    result = calculate_value_bet(match)
                    if result:
                        all_matches.append(result)
                
                progress_bar.progress((idx + 1) / total_leagues)
                
            except Exception as e:
                logger.error(f"Грешка при обработка на {league}: {str(e)}")
                continue
        
        progress_bar.empty()
        
        if not all_matches:
            st.warning("""
                🧐 Няма намерени value bets. Възможни причини:
                1. Всички коефициенти са точни според модела
                2. Липса на достатъчно исторически данни
                3. Висок праг за минимален value
                """)
            return
            
        # Създай DataFrame
        df = pd.DataFrame(all_matches).sort_values(["Value Домакин", "Value Равен", "Value Гост"], ascending=False)
        
        # Стилизиране
        def color_value(value):
            color = 'green' if value >= VALUE_THRESHOLD else 'red' if value <= -VALUE_THRESHOLD else 'black'
            return f'color: {color}'
        
        styled_df = df.style.map(color_value, subset=["Value Домакин", "Value Равен", "Value Гост"])
        
        # Покажи резултатите
        st.dataframe(
            styled_df.format({
                "Value Домакин": "{:.2%}",
                "Value Равен": "{:.2%}",
                "Value Гост": "{:.2%}",
                "Коеф. Домакин": "{:.2f}",
                "Коеф. Равен": "{:.2f}",
                "Коеф. Гост": "{:.2f}"
            }),
            column_config={
                "Форма Домакин": "Последни 5 (Д)",
                "Форма Гост": "Последни 5 (Г)"
            },
            hide_index=True,
            use_container_width=True,
            height=800
        )
        
        # Статистики
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Общо мачове", len(all_matches))
        with col2:
            st.metric("Намерени лиги", f"{len(leagues)}/{total_leagues}")
        with col3:
            st.metric("Последно обновяване", datetime.now(LOCAL_TZ).strftime("%H:%M:%S"))
        
    except Exception as e:
        st.error(f"Критична грешка: {str(e)}")
        logger.exception("Грешка в основния поток")

if __name__ == "__main__":
    main()
