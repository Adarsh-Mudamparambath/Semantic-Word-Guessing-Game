# Architecture

## Overview

```
Browser (React)
      │  HTTP + session cookie
      v
FastAPI backend
      │
      ├── game_service.py    daily word selection, guess submission, dedup
      ├── scoring.py          normalize -> exact-match -> cache -> LLM judge -> calibrate
      └── SQLAlchemy models   words, daily_games, player_sessions, guesses, score_cache
      │
      v
PostgreSQL
```

## Why an LLM judge instead of a local embedding model

The original spec calls for a pretrained sentence-embedding model +
cosine similarity + a calibration layer. That is still the intended
production design (`SCORING_BACKEND=sentence_transformers`), but this
codebase was built in a sandboxed environment without access to
huggingface.co, so model weights couldn't be downloaded here.

Instead, `SCORING_BACKEND=llm_judge` (the default) asks a Claude model to
output a single calibrated 0–100 semantic-closeness score per (secret,
guess) pair, anchored with the same few-shot examples from the spec
(ocean/beach -> 82, etc). This satisfies every game rule — semantics only,
never spelling, exact match always 100, output clamped to [0, 100] — with
zero model download.

**Swapping to a real embedding model later:** implement the function body
in `app/scoring.py::score_sentence_transformers` (the interface and a
worked example are already there), set `SCORING_BACKEND=sentence_transformers`
in `.env`, and nothing else in the app changes — `game_service.py` and the
API only ever call `scoring.calculate_score()`.

## Score pipeline

```
guess text
    │
normalize()                     lowercase, trim, strip to a-z
    │
exact match secret? ──yes──► 100
    │ no
DB score_cache lookup ──hit──► cached score   (shared across ALL players)
    │ miss
in-process LRU (scoring.py)  ──hit──► cached score
    │ miss
scoring backend (llm_judge)
    │
clamp [0, 100], guard: non-exact guess can never show 100
    │
write-through DB cache
```

Because the secret word list is fixed for a given day and guesses cluster
heavily around common words ("water", "animal", "thing"...), the two-level
cache means the scoring backend is hit far less than once per guess in
practice.

## Daily word selection

`game_service.get_or_create_daily_game()` is idempotent per date: the first
request for a given day picks a random *active* word that hasn't been used
in the last 60 days, and every subsequent request that day reuses the same
`daily_games` row. Admins can force a specific word via
`set_daily_game_override()`.

## Security model

- Secret word and its id are never serialized into any API response.
- Sessions are random UUIDs in an httpOnly cookie — not guessable, no PII.
- All win/score/game-state logic is computed server-side; the frontend only
  renders what the API returns.
- Rate limiting is a per-session sliding window (`app/security.py`); swap
  the in-memory store for Redis if running multiple backend workers.

## Extensibility

- **Random / Custom modes**: `daily_games` already models "one row = one
  word for one context"; a `game_mode` column plus a session-scoped table
  for random/custom games slots in without touching the scoring engine.
- **User accounts**: `player_sessions` is deliberately anonymous-only for
  the MVP; a nullable `user_id` FK is the only schema change needed to
  attach accounts later.
- **pgvector**: reserved in `docker-compose.yml` (the `pgvector/pgvector`
  Postgres image) for when `SCORING_BACKEND=sentence_transformers` is
  enabled and secret-word embeddings are stored for fast lookup.
