import streamlit as st
import requests

API_KEY = "2e086a4b6d758dec878ee7b5593405b1"

def get_sports():
    url = f"https://api.the-odds-api.com/v4/sports?apiKey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        sports = response.json()
        return sports
    except requests.exceptions.RequestException as e:
        st.error(f"Грешка при зареждане на спортове: {e}")
        return []

def main():
    st.title("Актуални спортове и лиги от The Odds API")
    sports = get_sports()
    if sports:
        st.write("Намерени спортове и първенства:")
        for sport in sports:
            st.write(f"- {sport['key']} : {sport['title']}")
    else:
        st.write("Няма намерени спортове.")

if __name__ == "__main__":
    main()
