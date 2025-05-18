// Основен JavaScript код за анализ и показване на стойностни залози
// Включва пазари 1X2, над/под 2.5, гол/гол и очаквана стойност

const API_KEY = 'ТВОЯТ_API_КЛЮЧ';
const SPORTS = [
  'soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a',
  'soccer_germany_bundesliga', 'soccer_france_ligue_one',
  'soccer_netherlands_eredivisie', 'soccer_portugal_primeira_liga',
  'soccer_greece_super_league', 'soccer_austria_bundesliga',
  'soccer_switzerland_superleague', 'soccer_czech_czech_liga',
  'soccer_poland_ekstraklasa', 'soccer_croatia_1_hnl'
];

const MARKETS = ['h2h', 'totals', 'both_teams_to_score'];
const VALUE_THRESHOLD = 1.05; // Минимална стойност за валиден стойностен залог

async function fetchOddsForSport(sport) {
  const url = `https://api.the-odds-api.com/v4/sports/${sport}/odds/?apiKey=${API_KEY}&regions=eu&markets=${MARKETS.join(',')}&oddsFormat=decimal&dateFormat=iso`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Грешка при зареждане на ${sport}`);
  return response.json();
}

function calculateValue(odds, impliedProb) {
  return odds * impliedProb;
}

function getMarketValueBet(market, outcomes) {
  let best = null;
  outcomes.forEach(o => {
    const implied = 1 / o.odds;
    const value = calculateValue(o.odds, implied);
    if (value >= VALUE_THRESHOLD) {
      if (!best || value > best.value) {
        best = { name: o.name, odds: o.odds, value, market };
      }
    }
  });
  return best;
}

async function loadValueBets() {
  const results = [];
  for (let sport of SPORTS) {
    try {
      const games = await fetchOddsForSport(sport);
      games.forEach(game => {
        const { home_team, away_team, bookmakers, commence_time } = game;
        bookmakers.forEach(bm => {
          bm.markets.forEach(mkt => {
            const bet = getMarketValueBet(mkt.key, mkt.outcomes);
            if (bet) {
              results.push({
                home: home_team,
                away: away_team,
                bookmaker: bm.title,
                commence_time,
                ...bet
              });
            }
          });
        });
      });
    } catch (e) {
      console.warn(e.message);
    }
  }

  displayValueBets(results);
}

function displayValueBets(bets) {
  const container = document.getElementById('value-bets');
  container.innerHTML = '';
  if (bets.length === 0) {
    container.innerHTML = '<p>Няма открити стойностни залози за днес.</p>';
    return;
  }

  bets.sort((a, b) => b.value - a.value);
  bets.forEach(bet => {
    const row = document.createElement('div');
    row.className = 'bet-row';
    row.innerHTML = `
      <strong>${bet.home} vs ${bet.away}</strong><br>
      Час: ${new Date(bet.commence_time).toLocaleString()}<br>
      Пазар: ${bet.market} | Залог: ${bet.name}<br>
      Букмейкър: ${bet.bookmaker}<br>
      Коефициент: ${bet.odds} | Стойност: ${bet.value.toFixed(2)}
      <hr>
    `;
    container.appendChild(row);
  });
}

document.addEventListener('DOMContentLoaded', loadValueBets);
