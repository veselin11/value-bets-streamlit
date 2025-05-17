import requests
import pandas as pd
import streamlit as st
import os

BASE_URL = "https://v3.football.api-sports.io"
API_KEY = st.secrets.get("API_KEY") or os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("Не е зададен API_KEY в средата на изпълнение!")

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}

def get_upcoming_matches(league_ids=None, count=10):
    """
    Връща предстоящи мачове от избрани лиги (или всички, ако няма подадени).
    """
    matches = []

    url = f"{BASE_URL}/fixtures?next={count}"
    res = requests.get(url, headers=headers)

    # Диагностика
    st.write("🔍 Статус код на API заявката:", res.status_code)

    try:
        response_data = res.json()
    except Exception as e:
        st.error("Грешка при четене на JSON отговора от API-то.")
        return pd.DataFrame()

    st.write("📦 Пълно съдържание на отговора:")
    st.json(response_data)

    if res.status_code != 200:
        st.error(f"⚠️ API заявката се провали. Код: {res.status_code}")
        return pd.DataFrame()

    data = response_data.get("response", [])
    if not data:
        st.warning("⚠️ API не върна никакви мачове.")
        return pd.DataFrame()

    for match in data:
        try:
            league_id = match["league"]["id"]
            if league_ids and league_id not in league_ids:
                continue

            matches.append({
                "Отбор 1": match["teams"]["home"]["name"],
                "Отбор 2": match["teams"]["away"]["name"],
                "Лига": match["league"]["name"],
                "Дата": match["fixture"]["date"][:10],
                "Коеф": 2.5  # Фиктивен коефициент
            })
        except Exception as e:
            st.warning(f"⚠️ Проблем с един от мачовете: {e}")
            continue

    if not matches:
        st.warning("❗ Няма мачове, които да отговарят на условията.")
        return pd.DataFrame()

    return pd.DataFrame(matches)
