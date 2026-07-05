# Saville Fraud Royale Detector

A rule-based Clash Royale deck autopsy built from battle-log receipts.

No LLMs. Only receipts.

The app produces an entertainment report from deterministic backend rules, local card metadata, a local community-meme taxonomy, recent battle-log results, deck composition, matchup recurrence, and level context. It is not a skill rating or cheating detector.

## What The Report Shows

- Player identity, trophies when available, matches analysed, and confidence.
- Fraud Score: an entertainment index based on deck traits, recent battle-log evidence, level context, and recurring matchup patterns.
- Current deck profile with card icons or initials fallback, archetype estimate, average elixir, usage context, and one deck-specific roast.
- Exactly three default evidence cards with observed fact, sample size, confidence, score impact, roast, and expandable receipts.
- One optional level-context chart when enough level-known standard 1v1 matches exist.
- Compact data limits and report schema disclosure.

## Data Limits

The Clash Royale battle log does not include replay footage, card placements, elixir spending, card timing, card-cast counts, or exact in-match decisions.

The app must not claim that a player panicked, cheated, intentionally relied on levels, or made a specific in-match decision. The report states observed battle-log facts first, then attaches a joke.

## Data Modes

The backend supports both modes:

- `USE_MOCK_DATA=true`: local demo victims and generated mock battle logs.
- `USE_MOCK_DATA=false`: real Clash Royale API calls from the FastAPI backend.

The frontend never receives the Clash Royale API key. Keep secrets in the project root `.env` or another backend-only environment source. Do not commit `.env`.

## Report Contract

Current report schema: `report-v7`.

The backend response includes `structured_evidence` entries:

```json
{
  "id": "level_context",
  "title": "Level context",
  "observation": "Level-known overlevelled record: 7-3 with average loss level difference +0.59.",
  "sample_size": 23,
  "confidence": "high",
  "score_impact": 14,
  "roast_key": "level_context_v2",
  "roast_text": "Your cards arrived with a height advantage and the confidence of a private-school bully.",
  "receipts": []
}
```

The frontend validates reports at runtime with Zod. If the backend returns an unexpected shape, the UI shows a clear "Report data could not be read" error instead of inventing a fake complete report.

## Cache Behaviour

SQLite caching is kept. Report cache identity includes:

- player tag
- analysis/report schema version
- community taxonomy version
- Goblin Mode
- source mode (`mock` or `real`)
- seed

This prevents stale reports from old scoring rules or taxonomy files from being reused after analysis changes.

## Setup

```powershell
cd C:\Users\hp\Documents\Codex\2026-06-30\re\saville-fraud-royale-detector
```

Backend:

```powershell
cd backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open:

```text
http://127.0.0.1:5173/
```

If port `8000` is unavailable, run the backend on another port and set `VITE_API_BASE_URL` before starting Vite.

## Quality Checks

Backend:

```powershell
py -m compileall backend\app
py -m unittest discover backend\tests
```

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```

`npm run test` currently uses a lightweight Node test harness for contract/static UI checks. Attempts to install the full Vitest + React Testing Library stack stalled in this local npm environment; the scripts still provide executable frontend checks, while TypeScript and production build validate the split React code.

## API

```text
GET /api/health
GET /api/demo-victims
GET /api/reports/{player_tag}?goblin_mode=false&seed=saville
```

Real Clash Royale mode calls the official API only from the backend:

```text
GET /v1/players/%23{player_tag}
GET /v1/players/%23{player_tag}/battlelog
```

## Community Meme Taxonomy

Community deck stereotypes live in:

```text
data/community_meme_taxonomy.json
```

These are player-community jokes, not objective skill facts. Update the taxonomy manually, keep source notes honest, and avoid identity-based, sexual, hateful, threatening, or personal harassment language.
