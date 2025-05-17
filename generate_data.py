import pandas as pd
import random

teams = [
    "Левски", "ЦСКА", "Локомотив Пловдив", "Берое", "Ботев Пловдив",
    "Барселона", "Реал Мадрид", "Атлетико Мадрид",
    "Манчестър Юн.", "Арсенал", "Ливърпул", "Челси",
    "Байерн", "Борусия Дортмунд"
]

leagues = [
    "Първа лига", "Ла Лига", "Висша лига", "Бундеслига"
]

data = []

for _ in range(100):
    team1 = random.choice(teams)
    team2 = random.choice([t for t in teams if t != team1])
    league = random.choice(leagues)
    coef = round(random.uniform(1.5, 3.5), 2)

    # Примерна логика за стойностен залог (ако коеф >= 2.2 и случайно 40% от тези случаи са value bets)
    if coef >= 2.2 and random.random() < 0.4:
        value_bet = 1
    else:
        value_bet = 0

    data.append([team1, team2, league, coef, value_bet])

df = pd.DataFrame(data, columns=["Отбор 1", "Отбор 2", "Лига", "Коеф", "ValueBet"])
df.to_csv("football_data.csv", index=False)

print("Файлът football_data.csv е генериран успешно!")
