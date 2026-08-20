"""
Semantic similarity scoring engine.

Architecture (see docs/architecture.md):

    guess + secret word
            v
    normalize()
            v
    exact-match shortcut  ---- match --> 100
            v no match
    ScoreCache (DB) lookup ---- hit --> cached score
            v miss
    in-process LRU lookup ---- hit --> cached score
            v miss
    scoring backend (pluggable)
            v
    calibrate + clamp to [0, 100]
            v
    write-through both caches

The scoring backend uses pre-computed sentence-transformer embeddings and
cosine similarity. Scores are calibrated to the game's 0-100 range.

Do NOT use spelling/edit-distance similarity anywhere in this module.
"""

import json
import re
from typing import TYPE_CHECKING

import numpy as np

from app.config import get_settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

settings = get_settings()

def normalize(word: str) -> str:
    """Lowercase, trim, strip to letters only. Same normalization for
    secret words and guesses so 'Ocean', ' ocean ', 'OCEAN' all match."""
    word = word.strip().lower()
    word = re.sub(r"[^a-z]", "", word)
    return word


# ---------------------------------------------------------------------------
# sentence-transformers backend
# ---------------------------------------------------------------------------

_embedding_model = None


def _get_embedding_model():
    """Lazy-load the embedding model once."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


def _get_embedding_for_word(word: str, db: "Session") -> np.ndarray | None:
    """Fetch pre-computed embedding for a normalized word from the database."""
    if db is None:
        raise ValueError("A database session is required for semantic scoring.")
    
    from sqlalchemy import select
    from app import models
    
    # Find the word in the database
    word_row = db.execute(
        select(models.Word).where(models.Word.normalized_word == word)
    ).scalar_one_or_none()
    
    if word_row is None:
        return None
    
    # Find the embedding for this word
    embedding_row = db.execute(
        select(models.WordEmbedding).where(
            models.WordEmbedding.word_id == word_row.id,
            models.WordEmbedding.model_name == settings.embedding_model,
        )
    ).scalar_one_or_none()
    
    if embedding_row is None:
        return None
    
    # Parse the JSON-encoded embedding
    try:
        embedding_list = json.loads(embedding_row.embedding)
        return np.array(embedding_list, dtype=np.float32)
    except (json.JSONDecodeError, ValueError):
        return None


def _calibrate_cosine_to_score(cosine_similarity: float) -> int:
    """Convert cosine similarity [-1, 1] to a game score [0, 100].
    
    Cosine similarity for related words is typically in [0.2, 1.0].
    This calibrates using the examples from the game-mechanics.
    """
    # Typical range for semantically related words is [0.2, 1.0]
    # Map [0.2, 1.0] -> [0, 100], with values below 0.2 -> very cold
    if cosine_similarity < 0.0:
        cosine_similarity = 0.0
    
    # Simple linear mapping: 0.2 -> 0, 1.0 -> 100
    # For values below 0.2, use a steeper curve
    if cosine_similarity < 0.2:
        score = cosine_similarity * 50  # [0, 0.2] -> [0, 10]
    else:
        # [0.2, 1.0] -> [10, 100]
        score = 10 + (cosine_similarity - 0.2) * (100 - 10) / (1.0 - 0.2)
    
    return int(round(score))


def score_sentence_transformers(secret_normalized: str, guess_normalized: str, db: "Session | None" = None) -> int:
    """Score using pre-computed semantic embeddings and cosine similarity.
    
    This requires pre-computed word embeddings and a database session.
    """
    if db is None:
        raise ValueError("A database session is required for semantic scoring.")
    
    # Get embeddings for both words
    secret_embedding = _get_embedding_for_word(secret_normalized, db)
    guess_embedding = _get_embedding_for_word(guess_normalized, db)
    
    if secret_embedding is None or guess_embedding is None:
        raise RuntimeError(
            "A semantic embedding is missing. Run backend/scripts/precompute_embeddings.py."
        )
    
    secret_norm = np.linalg.norm(secret_embedding)
    guess_norm = np.linalg.norm(guess_embedding)
    if secret_norm == 0 or guess_norm == 0:
        raise RuntimeError("Cannot score a zero-length semantic embedding.")
    cosine_sim = float(np.dot(secret_embedding, guess_embedding) / (secret_norm * guess_norm))
    
    # Calibrate to [0, 100] score
    score = _calibrate_cosine_to_score(cosine_sim)
    
    return score


SCORING_BACKENDS = {
    "sentence_transformers": score_sentence_transformers,
}


def _fallback_score(secret_normalized: str, guess_normalized: str) -> int:
    """Compatibility helper: never infer meaning from spelling."""
    return 0


def calculate_score(secret_word: str, guess: str, db: "Session | None" = None) -> int:
    """Public entry point: normalize, exact-match shortcut, then delegate
    to the configured scoring backend. Always returns an int in [0, 100].
    
    Args:
        secret_word: The secret word to compare against
        guess: The guessed word
        db: Database session used to retrieve semantic embeddings.
    
    Returns:
        An integer score in [0, 100]
    """
    secret_normalized = normalize(secret_word)
    guess_normalized = normalize(guess)

    if not guess_normalized:
        return 0

    if guess_normalized == secret_normalized:
        return 100

    backend = SCORING_BACKENDS.get(settings.scoring_backend)
    if backend is None:
        raise ValueError(f"Unknown SCORING_BACKEND: {settings.scoring_backend}")

    score = backend(secret_normalized, guess_normalized, db)

    score = max(0, min(100, int(score)))

    # Guard: only the true secret word may ever show 100.
    if score >= 100 and guess_normalized != secret_normalized:
        score = 99

    return score


def get_feedback(score: int) -> str:
    """Configurable threshold -> feedback text, from settings.feedback_thresholds."""
    thresholds = sorted(settings.feedback_thresholds.items())
    label = thresholds[0][1]
    for cutoff, text in thresholds:
        if score >= cutoff:
            label = text
    return label
