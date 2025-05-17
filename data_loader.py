import requests
import pandas as pd
from datetime import date

API_KEY = "685e423d2d9e078e7c5f7f9439e77f7c"
API_URL = "https://v3.football.api-sports.io/fixtures"

HEADERS = {
    'x-apisports-key': API_KEY
}

def load_matches_from_api(selected_date: date):
    try:
        params = {
            'date': selected_date.isoformat(),
            # Може да добавиш още филтри, напр. 'league' или 'season'
        }
        response = requests.get(API_URL, headers=HEADERS, params=params)
        data = response.json()

        if not data['response']:
            print(f"Няма мачове за дата {selected_date}")
            return pd.DataFrame()

        matches = []
        for item in data['response']:
            fixture = item['fixture']
            league = item['league']['name']
            teams = item['teams']
            odds = item.get('odds', [])

            # Опитваме се да вземем коефициенти на пазара 1X2 (ако има)
            coef = None
            for bookie in item.get('bookmakers', []):
                for market in bookie['bets']:
                    if market['name'] == 'Match Winner':
                        # Взимаме коефициенти за домакин, равен, гост
                        for val in market['values']:
                            if val['value'] == 'Home':
                                coef = val['odd']
                                break
                        if coef:
                            break
                if coef:
                    break

            if coef is None:
                # Ако няма коефициент, пропускаме
                continue

            matches.append({
                "Отбор 1": teams['home']['name'],
                "Отбор 2": teams['away']['name'],
                "Лига": league,
                "Коеф": float(coef),
                "Дата": pd.to_datetime(fixture['date']).date()
            })

        df = pd.DataFrame(matches)
        print(f"Заредени {len(df)} мача от API за дата {selected_date}")
        return df

    except Exception as e:
        print(f"Грешка при зареждане на мачове от API: {e}")
        return pd.DataFrame()
