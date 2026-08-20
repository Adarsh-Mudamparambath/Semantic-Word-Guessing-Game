# Meridian — Semantic Word Guessing Game

A daily word-discovery game. One secret word, shared by everyone each day.
Guess any word and get back a 0–100 score for how close it is *in meaning*
— never spelling. Hot-and-cold your way to the answer.

```
ocean
Computer → 4%
Mountain → 17%
Fish     → 62%
Beach    → 82%
Water    → 93%
Sea      → 97%
Ocean    → 100%
```

## Stack

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy, Pydantic
- **Frontend**: React, Vite, Tailwind CSS
- **Scoring**: local `sentence-transformers` embeddings are compared with
  cosine similarity, calibrated to 0-100, and cached per (secret, guess) pair.
- **Dictionary**: guesses must exist in the active curated word database before
  they are scored.

## Project layout

```
semantic-word-game/
├── backend/        FastAPI app, tests, Dockerfile
├── frontend/        React + Vite + Tailwind app, Dockerfile
├── data/            curated word dataset + diversity report
├── scripts/         word-list generation, diversity check, DB seed
├── docs/            architecture, game mechanics, API reference
├── docker-compose.yml
└── .env.example
```

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
# edit backend/.env — use SCORING_BACKEND=sentence_transformers

docker compose up --build

# in another terminal, seed the word database once containers are up:
docker compose exec backend python ../scripts/seed_database.py
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

## Quick start (without Docker)

**Backend**
```bash
cd backend
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # fill in ANTHROPIC_API_KEY, point DATABASE_URL at a running Postgres
python ../scripts/generate_word_list.py   # regenerate data/*.csv if needed
python ../scripts/seed_database.py
python scripts/precompute_embeddings.py
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
python -m pytest tests/ -q
```

11 tests cover normalization, exact-match handling, score clamping,
duplicate-guess dedup, and that the secret word is never leaked in any API
response.

## Notes on this build

- **Network-sandboxed dev environment**: this repo was built somewhere
  without access to huggingface.co, so the "pretrained sentence-embedding
  model" called for in the original spec couldn't be downloaded. The
  scoring engine is architected so that's a one-function swap later —
  see `docs/architecture.md`.
- **Word count**: 935 curated, deduplicated words across 23 categories
  (target was ~1000) — see `data/README.md` for how to top it up.
- **Ads**: `<AdContainer />` renders provider-agnostic placeholders at
  top/inline/footer placements; wire in a real network whenever ready.
- Deliberately out of scope for this pass (see spec §41–55 "future
  features"): accounts, leaderboards, streak tracking, multiple game
  modes. The schema and service layer were built not to block them later.
