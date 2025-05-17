import pandas as pd

def implied_probability(odds):
    """Пресмята имплицитна вероятност от коефициент."""
    return 1 / odds if odds > 0 else 0

def predict(df: pd.DataFrame, min_value=5):
    """
    Оценява стойностни залози (value bets).
    df: DataFrame с мачове, трябва да съдържа колони: 'Отбор 1', 'Отбор 2', 'Коеф'
    min_value: минимален value % за включване в резултатите
    """

    predictions = []

    for _, row in df.iterrows():
        # Симулирана вероятност (в бъдеще ще се замени с ML модел)
        est_prob = 0.45  # 45% вероятност за успех (примерно)

        odds = row['Коеф']
        implied_prob = implied_probability(odds)
        value = (est_prob * odds - 1) * 100  # Value в проценти

        if value >= min_value:
            predictions.append({
                "Отбор 1": row['Отбор 1'],
                "Отбор 2": row['Отбор 2'],
                "Дата": row['Дата'],
                "Лига": row['Лига'],
                "Коеф": odds,
                "Вероятност": f"{est_prob:.0%}",
                "Имплицитна вероятност": f"{implied_prob:.0%}",
                "Value %": round(value, 2)
            })

    return pd.DataFrame(predictions)
