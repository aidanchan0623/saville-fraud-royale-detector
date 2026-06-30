# Architecture Notes

Saville Fraud Royale Detector is split into a backend rule engine and a frontend report dashboard.

## Backend Flow

1. `app.routers.reports` receives a player tag.
2. `app.services.clash_api` either calls the official Clash Royale API or expands local mock scenarios.
3. `app.services.card_data_service` hydrates card names with elixir, rarity, type, and traits.
4. `app.services.analysis_service` computes battle, deck, matchup, level, behavior, clutch, and troll-score metrics.
5. `app.services.roast_engine` picks deterministic template text for the matched rules.
6. `app.db` caches report payloads in SQLite.

## Frontend Flow

1. The landing view submits a player tag and Goblin Mode setting.
2. `src/lib/api.ts` calls `/api/reports/{tag}`.
3. `src/App.tsx` renders the dashboard sections and charts from the structured report.

## Data Assumptions

The app never claims to inspect gameplay details that the battle log cannot expose. All claims should trace back to deck composition, battle result, crown counts, opponent cards, card levels, or repeated patterns in the recent battle log.

