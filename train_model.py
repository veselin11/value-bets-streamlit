import streamlit as st
import pandas as pd
import joblib
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Value Bets ML", layout="wide")

# Зареждане на ML модел и label encoder
@st.cache_resource
def load_model():
    model = joblib.load("value_bet_model.pkl")
    le = joblib.load("label_encoder.pkl")
    return model, le

model, le = load_model()

# Генериране на примерни залози
def generate_bets(n=40):
    leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']
    markets = ['1X2', 'Over/Under 2.5', 'Both Teams to Score']
    teams = ['Team A', 'Team B', 'Team C', 'Team D']
    picks = ['1', 'X', '2', 'Over 2.5', 'Under 2.5', 'Yes', 'No']
    rows = []
    for _ in range(n):
        team1, team2 = random.sample(teams, 2)
        match_time = datetime.now() + timedelta(hours=random.randint(1, 72))
        league = random.choice(leagues)
        market = random.choice(markets)
        pick = random.choice(picks)
        odds = round(random.uniform(1.5, 3.5), 2)
        rows.append({
            'league': league,
            'team1': team1,
            'team2': team2,
            'market': market,
            'pick': pick,
            'odds': odds,
            'match': f"{team1} - {team2}",
            'time': match_time.strftime('%Y-%m-%d %H:%M')
        })
    return pd.DataFrame(rows)

# Енкодиране на категориални характеристики с LabelEncoder
def encode_features(df, le):
    df_encoded = df.copy()
    for col in ['league', 'team1', 'team2', 'market', 'pick']:
        try:
            df_encoded[col] = le.transform(df_encoded[col].astype(str))
        except ValueError:
            # Ако има нова стойност, която не е в обучението, подменяме с някаква стойност (напр. 0)
            df_encoded[col] = 0
    return df_encoded

st.title("Value Bets с ML прогнози")
st.markdown("Препоръчани залози с прогнози от машинно обучение и изчислен Value %.")

min_value = st.slider("Минимален Value %", 0.0, 20.0, 4.0, step=0.5)
max_rows = st.slider("Макс. брой залози", 5, 50, 15)

bets_df = generate_bets()

try:
    X = encode_features(bets_df, le)[['league', 'team1', 'team2', 'market', 'pick', 'odds']]
except Exception as e:
    st.error(f"Грешка при енкодиране: {e}")
    st.stop()

pred_probs = model.predict_proba(X)[:, 1]
bets_df['Win Probability'] = (pred_probs * 100).round(2)
bets_df['Implied Probability'] = (1 / bets_df['odds'] * 100).round(2)
bets_df['Value %'] = (bets_df['Win Probability'] - bets_df['Implied Probability']).round(2)

value_bets = bets_df[bets_df['Value %'] > 0].sort_values('Value %', ascending=False).reset_index(drop=True)
filtered_bets = value_bets[value_bets['Value %'] >= min_value].head(max_rows)

st.subheader("Препоръчани залози с положителен Value %")
st.dataframe(filtered_bets[['match', 'time', 'league', 'market', 'pick', 'odds', 'Win Probability', 'Implied Probability', 'Value %']], use_container_width=True)

# История на залозите
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame()

if st.button("Добави показаните залози към историята"):
    st.session_state.history = pd.concat([st.session_state.history, filtered_bets]).drop_duplicates().reset_index(drop=True)

if not st.session_state.history.empty:
    st.subheader("История на залозите")
    st.dataframe(st.session_state.history, use_container_width=True)
