# Architecture

## Overview

```
Browser (React)
      │  HTTP + session cookie
      v
FastAPI backend
      │
      ├── game_service.py    daily word selection, guess submission, dedup
      ├── scoring.py          normalize -> exact-match -> cache -> embeddings -> cosine -> calibrate
      └── SQLAlchemy models   words, daily_games, player_sessions, guesses, score_cache
      │
      v
PostgreSQL
```

## Semantic scoring

The game uses the pretrained `sentence-transformers/all-MiniLM-L6-v2` model
locally. The setup script precomputes one vector for every active dictionary
word and stores it in `word_embeddings`. Each valid guess is scored by cosine
similarity against the secret word's vector, then calibrated to 0-100. No
Claude API or other remote scoring service is used.

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
scoring backend (sentence_transformers)
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
- **pgvector**: reserved in `docker-compose.yml`; embeddings currently use
  JSON storage and NumPy cosine similarity.
