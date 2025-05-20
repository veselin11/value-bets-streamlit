def calculate_implied_probability(odds):
    if odds <= 0:
        return 0
    return 1 / odds

def calculate_value_bets(odds, probability, threshold=0.05):
    value = odds * probability - 1
    return value > threshold, value

def get_team_stats(team_name, stats_data):
    for team in stats_data:
        if team.get("team_name", "").lower() == team_name.lower():
            return team
    return {}
