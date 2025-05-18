// Автоматичен анализатор на стойностни залози // Поддържани пазари: 1X2, Над/Под 2.5, Гол/Гол

const fetch = require("node-fetch"); const API_KEY = "YOUR_API_KEY"; const SPORTS = [ "soccer_epl", "soccer_uefa_champs_league", "soccer_italy_serie_a", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_france_ligue_one" ];

const TARGET_MARKETS = ["h2h", "totals", "btts"];

const MIN_VALUE_THRESHOLD = 1.05; // минимална стойност за стойностен залог const MIN_BOOKMAKERS = 2; // поне 2 различни букмейкъра

function calculateValue(odds, impliedProb) { return odds * impliedProb; }

function impliedProbability(odds) { return 1 / odds; }

async function fetchOddsForSport(sport) { const url = https://api.the-odds-api.com/v4/sports/${sport}/odds/?apiKey=${API_KEY}&regions=eu&markets=${TARGET_MARKETS.join(",")}&oddsFormat=decimal&dateFormat=iso; const res = await fetch(url); if (!res.ok) throw new Error(Грешка при зареждане: ${sport}); return res.json(); }

async function getValueBets() { let allValueBets = [];

for (const sport of SPORTS) { try { const matches = await fetchOddsForSport(sport); for (const match of matches) { const outcomes = {}; for (const bookmaker of match.bookmakers || []) { for (const market of bookmaker.markets || []) { for (const outcome of market.outcomes) { const key = ${market.key}_${outcome.name}; if (!outcomes[key]) outcomes[key] = []; outcomes[key].push(outcome.price); } } }

for (const [key, prices] of Object.entries(outcomes)) {
      if (prices.length < MIN_BOOKMAKERS) continue;
      const maxOdds = Math.max(...prices);
      const avgProb = prices.reduce((a, b) => a + impliedProbability(b), 0) / prices.length;
      const value = calculateValue(maxOdds, avgProb);

      if (value >= MIN_VALUE_THRESHOLD) {
        allValueBets.push({
          match: match.home_team + " vs " + match.away_team,
          time: match.commence_time,
          market: key,
          bestOdds: maxOdds.toFixed(2),
          value: value.toFixed(2)
        });
      }
    }
  }
} catch (err) {
  console.error(err.message);
}

}

return allValueBets; }

(async () => { const valueBets = await getValueBets(); if (valueBets.length === 0) { console.log("Няма открити стойностни залози за днес."); } else { console.log("Стойностни залози:"); valueBets.forEach((bet) => { console.log(${bet.match} | ${bet.market} | Коефициент: ${bet.bestOdds} | Стойност: ${bet.value}); }); } })();
