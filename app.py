import random
import datetime

# Настройки
bankroll = 500
bets_history = []

# Днешна дата
today = datetime.date.today()

# Днешни мачове (примерни)
todays_matches = [
    {"match": "Барселона vs Хетафе", "odds": 1.55, "prediction": "1", "selected": False},
    {"match": "Верона vs Болоня", "odds": 2.10, "prediction": "2", "selected": False},
    {"match": "Брюж vs Андерлехт", "odds": 2.45, "prediction": "X", "selected": False}
]

# Функция за залагане на мач
def place_bet(match_index, amount):
    global bankroll
    match = todays_matches[match_index]
    if match["selected"]:
        print(f"Вече си заложил на мача: {match['match']}")
        return

    win = random.random() < 1 / match["odds"]
    result = "Печалба" if win else "Загуба"
    if win:
        profit = amount * (match["odds"] - 1)
        bankroll += profit
    else:
        bankroll -= amount

    match["selected"] = True
    bets_history.append({
        "match": match["match"],
        "prediction": match["prediction"],
        "odds": match["odds"],
        "amount": amount,
        "result": result,
        "date": str(today)
    })
    print(f"{match['match']} | Прогноза: {match['prediction']} | Коефициент: {match['odds']} | {result} | Банка: {bankroll:.2f} лв.")

# Показване на днешни мачове
print("\n--- Днешни мачове ---")
for i, match in enumerate(todays_matches):
    print(f"{i + 1}. {match['match']} | Прогноза: {match['prediction']} | Коефициент: {match['odds']}")

# Примерен избор на залози
print("\n--- Изпълнение на залози ---")
place_bet(0, 100)
place_bet(1, 100)

# Статистика
print("\n--- История на залозите ---")
for bet in bets_history:
    print(f"{bet['date']} | {bet['match']} | {bet['prediction']} | {bet['odds']} | {bet['result']} | {bet['amount']} лв.")

print(f"\nТекуща банка: {bankroll:.2f} лв.")
