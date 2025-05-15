import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- Фиктивни данни ---
# Тук можете да заредите реални данни от CSV или API.
data = {
    'team1': ['Man City', 'Liverpool', 'Arsenal', 'Chelsea', 'Tottenham'],
    'team2': ['Man United', 'Everton', 'Leicester', 'West Ham', 'Aston Villa'],
    'odds_team1': [1.5, 2.3, 2.8, 2.0, 2.5],
    'odds_team2': [2.8, 3.0, 3.5, 2.5, 3.0],
    'value': [0.2, 0.15, 0.25, 0.1, 0.18],  # Value is a measure of expected profit.
    'date': [datetime.now()] * 5
}

# Създаване на DataFrame
df = pd.DataFrame(data)

# --- Функция за изчисляване на стойностни прогнози ---
def calculate_bet_amount(bankroll, value, odds):
    # Примерно изчисление за залог, взимайки предвид стойността и коефициента
    bet = bankroll * value * odds
    return bet

# --- Създаване на интерфейс ---
st.title('Стойностни залози - Премачове')
st.write('Извличане на стойностни залози в реално време.')

# Избиране на първенство (може да се добави пълна функционалност за първенства)
league = st.selectbox('Избери първенство', ['Английска Висша лига', 'Испанска Ла Лига', 'Германска Бундеслига'])

# Избиране на мач за залог
match = st.selectbox('Избери мач', df['team1'] + ' срещу ' + df['team2'])

# Промяна на началната банка
bankroll = st.number_input("Въведете начална банка", min_value=0, max_value=10000, value=1000)

# Избор на залог
bet_option = st.selectbox('Изберете залог', ['Отбор 1', 'Отбор 2'])

# Изчисляване на стойностния залог
selected_match = df[df['team1'] + ' срещу ' + df['team2'] == match]
value = selected_match['value'].values[0]
odds = selected_match['odds_team1'].values[0] if bet_option == 'Отбор 1' else selected_match['odds_team2'].values[0]
bet_amount = calculate_bet_amount(bankroll, value, odds)

# Показване на стойностния залог
st.write(f'Препоръчителен залог за {bet_option}: {bet_amount:.2f} лв.')

# Съхранение на залога
if st.button('Заложи'):
    st.write(f'Заложили сте {bet_amount:.2f} лв. на {bet_option}.')

# --- История на залозите ---
if 'history' not in st.session_state:
    st.session_state.history = []

# Записване в история
if st.button('Запиши в история'):
    st.session_state.history.append({
        'team1': selected_match['team1'].values[0],
        'team2': selected_match['team2'].values[0],
        'bet': bet_option,
        'amount': bet_amount,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# Показване на историята на залозите
st.subheader("История на залозите")
if st.session_state.history:
    history_df = pd.DataFrame(st.session_state.history)
    st.write(history_df)
else:
    st.write("Няма залози в историята.")
