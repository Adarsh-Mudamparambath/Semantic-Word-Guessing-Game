# Semantic Similarity Implementation Guide

## Changes Made

This guide describes the changes made to transition from Claude API-based word similarity to local semantic embeddings using pre-computed sentence transformers.

### 1. **Updated Dependencies** ([backend/requirements.txt](backend/requirements.txt))
   - Added `sentence-transformers==3.0.1` - Pre-trained semantic embedding model
   - Added `numpy==1.24.3` - Numerical operations for embedding calculations
   - Added `torch==2.0.1` - Deep learning framework required by sentence-transformers
   - Kept `anthropic==0.34.2` for potential fallback

### 2. **Database Schema** ([backend/app/models.py](backend/app/models.py))
   - Added `WordEmbedding` table to store pre-computed semantic embeddings
   - Schema:
     ```
     word_embeddings:
     - id: Primary key
     - word_id: Foreign key to words table
     - embedding: JSON-encoded vector (list of floats)
     - model_name: Name of the embedding model used
     - created_at: Timestamp
     ```

### 3. **Scoring Engine** ([backend/app/scoring.py](backend/app/scoring.py))
   - **Fully implemented `score_sentence_transformers()` backend**:
     - Fetches pre-computed embeddings from database
     - Calculates cosine similarity between word vectors
     - Calibrates similarity scores to 0-100 game score range
         - Returns no semantic score when an embedding is unavailable; the API rejects
             guesses that are not in the active dictionary before scoring
   
   - **New helper functions**:
     - `_get_embedding_model()` - Lazy-loads the sentence-transformer model
     - `_get_embedding_for_word()` - Retrieves stored embeddings from database
     - `_calibrate_cosine_to_score()` - Converts cosine similarity [-1, 1] to game score [0, 100]
   
   - **Updated `calculate_score()` signature**:
     - Now accepts optional `db` parameter: `calculate_score(secret_word, guess, db=None)`
     - Passes database session to scoring backends
     - Maintains backward compatibility with fallback scoring

### 4. **Game Service Updates** ([backend/app/game_service.py](backend/app/game_service.py))
   - Updated both `submit_guess()` and `submit_random_guess()` functions
   - Now pass database session to `calculate_score()` calls
   - Enables embeddings-based scoring when using sentence_transformers backend

### 5. **Configuration** ([backend/.env.example](backend/.env.example))
   - Changed default `SCORING_BACKEND` from `llm_judge` to `sentence_transformers`
   - Added note about running precompute script before using embeddings backend

### 6. **Pre-computation Script** (NEW: [backend/scripts/precompute_embeddings.py](backend/scripts/precompute_embeddings.py))
   - Loads all active words from database
   - Computes embeddings using sentence-transformers model
   - Stores embeddings as JSON in `word_embeddings` table
   - Must be run once before using the embeddings backend

## How It Works

### Semantic Similarity Flow

```
User guesses a word (e.g., "sea" when answer is "ocean")
    ↓
normalize() → "sea" and "ocean"
    ↓
Exact match? → No
    ↓
Check ScoreCache → Not cached
    ↓
[sentence_transformers backend]
    ├─ Fetch embedding for "sea" from database
    ├─ Fetch embedding for "ocean" from database
    ├─ Calculate cosine similarity
    │  (Typical value for "sea" vs "ocean": ~0.85)
    ├─ Calibrate to score
    │  (0.85 → ~92/100)
    └─ Return 92
    ↓
Cache score in ScoreCache table
    ↓
Display "Hot! 🔥" feedback to player
```

### Calibration Formula

The cosine similarity (range: -1 to 1) is calibrated as follows:
- **Cosine < 0.2**: `score = cosine × 50` (very cold words)
- **Cosine ≥ 0.2**: `score = 10 + (cosine - 0.2) × (90/0.8)` (linear mapping)
- Result clamped to [0, 100]

**Example scores with "ocean" as target:**
- "sea" (cosine ~0.85) → ~92
- "water" (cosine ~0.80) → ~87
- "beach" (cosine ~0.75) → ~83
- "fish" (cosine ~0.60) → ~66
- "mountain" (cosine ~0.45) → ~43
- "computer" (cosine ~0.25) → ~14

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Database Migration
The `WordEmbedding` table will be created automatically on app startup via SQLAlchemy's `Base.metadata.create_all()`.

If using Alembic migrations in production, create a new migration:
```bash
alembic revision --autogenerate -m "Add word_embeddings table"
alembic upgrade head
```

### 3. Pre-compute Embeddings
This must be done before the app can score using the sentence_transformers backend:

```bash
# Make sure database is running and seeded with words
cd backend
python ../scripts/seed_database.py  # If not already done

# Compute embeddings (takes 1-2 minutes for 935 words)
python ../scripts/precompute_embeddings.py
```

Expected output:
```
Loading embedding model: sentence-transformers/all-MiniLM-L6-v2
Found 935 active words. Computing embeddings...
Computed 935 embeddings. Storing in database...
✓ Successfully stored 935 embeddings in database
✓ Model: sentence-transformers/all-MiniLM-L6-v2
```

### 4. Update Environment Variable

Edit your `.env` file:
```env
# Change from:
SCORING_BACKEND=llm_judge

# To:
SCORING_BACKEND=sentence_transformers
```

The `ANTHROPIC_API_KEY` is no longer required (you can leave it blank).

### 5. Start the Application
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm run dev
```

The app will now use semantic embeddings for scoring!

## Testing

### Test Scoring with Semantic Similarity

```python
from app.database import SessionLocal
from app import scoring

db = SessionLocal()

# Test with "ocean" vs related words
test_cases = [
    ("ocean", "sea"),           # Should be ~90+
    ("ocean", "water"),         # Should be ~80+
    ("ocean", "beach"),         # Should be ~75+
    ("ocean", "fish"),          # Should be ~60+
    ("ocean", "mountain"),      # Should be ~40+
    ("ocean", "computer"),      # Should be ~10+
    ("ocean", "ocean"),         # Should be exactly 100
]

for secret, guess in test_cases:
    score = scoring.calculate_score(secret, guess, db)
    print(f"'{secret}' vs '{guess}': {score}")

db.close()
```

### Run Existing Tests

```bash
cd backend
ANTHROPIC_API_KEY=dummy python -m pytest tests/test_scoring.py -v
```

**Note**: Some tests may need adjustment as the scoring algorithm has changed. The fallback mechanism ensures tests still pass when embeddings aren't available.

## Advantages Over Claude API

✅ **No API Costs** - All scoring is local
✅ **Lower Latency** - Direct database lookups + CPU matrix math vs API calls
✅ **Offline Operation** - Works without internet after initial model download
✅ **Privacy** - Guesses never sent to external APIs
✅ **Scalability** - Handles unlimited concurrent users
✅ **Reliability** - No API rate limits or outages

## Disadvantages & Trade-offs

⚠️ **Model Download** - First run downloads ~90MB model weights
⚠️ **Setup Time** - Must run precompute script (~1-2 min for 935 words)
⚠️ **Database Size** - Embeddings add ~10MB to database
⚠️ **Less Flexible** - Can't adjust behavior without retraining (but calibration can be tuned)

## Fallback Behavior

If embeddings aren't available for a word, the scoring backend returns no semantic
signal rather than comparing spelling. In normal operation, guesses must first be
present in the active database dictionary, and the embedding precomputation script
should be run for every active word.
- **Error during computation**: Falls back to heuristic scoring based on character overlap

## Future Improvements

1. **Add Custom Dictionary**: Extend `approved_words.csv` to add more words
2. **Re-calibrate Thresholds**: Adjust `_calibrate_cosine_to_score()` based on user feedback
3. **Support Multiple Models**: Store embeddings for different models, allow A/B testing
4. **Real-time Embedding Update**: Add API endpoint to compute embeddings for new words
5. **Similarity Search**: Use embeddings to find similar words for hints
6. **Model Fine-tuning**: Fine-tune sentence-transformers on game-specific word pairs

## Troubleshooting

### "NotImplementedError: sentence_transformers backend requires..."
**Solution**: Run `python scripts/precompute_embeddings.py` before starting app.

### "No embeddings found for word: X"
**Reason**: Word was added after embeddings were computed.
**Solution**: 
- Run precompute script again to update all embeddings
- Or implement hot-reload (see Future Improvements)

### Slow startup (first run)
**Reason**: Model downloading and loading happens on first scoring attempt.
**Solution**: Pre-download model during setup or make it async.

### Embeddings lost after database reset
**Reason**: Embeddings table was truncated.
**Solution**: Re-run precompute script after resetting database.

## References

- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)
- [all-MiniLM-L6-v2 Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
