# API Reference

Base URL: `http://localhost:8000`

All game endpoints set/read an httpOnly `swg_session` cookie — the
frontend must send credentials (`fetch(..., { credentials: "include" })`).

## `GET /api/game/today`

Returns today's game id. Never includes the secret word.

**Response 200**
```json
{ "game_id": "3f1c...", "date": "2026-08-13" }
```

## `POST /api/game/guess`

**Request**
```json
{ "game_id": "3f1c...", "guess": "beach" }
```

**Response 200**
```json
{
  "guess": "beach",
  "score": 82,
  "feedback": "🔥🔥 Hot",
  "is_correct": false,
  "guesses_remaining": null
}
```

**Errors**
- `422` — guess too short/long or empty (`{"detail": "Please enter a valid word."}`)
- `404` — unknown `game_id`
- `429` — rate limited (`guess_rate_limit_per_minute`, default 30/min per session)

## `GET /api/game/history?game_id=...`

**Response 200**
```json
{
  "game_id": "3f1c...",
  "guesses": [
    { "guess": "computer", "score": 4, "is_correct": false },
    { "guess": "beach", "score": 82, "is_correct": false }
  ],
  "best_score": 82,
  "solved": false
}
```

## `GET /api/health`

Liveness check — `{"status": "ok"}`.
