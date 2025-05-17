import pandas as pd
from datetime import date

def load_matches_from_api(selected_date: date):
    # TODO: Добави реален API call тук (пример под)
    try:
        df = pd.read_csv("matches_to_predict.csv")  # Симулирано зареждане
        df["Дата"] = pd.to_datetime(df["Дата"]).dt.date
        return df[df["Дата"] == selected_date]
    except Exception as e:
        print(f"Грешка при зареждане на мачове: {e}")
        return pd.DataFrame()
