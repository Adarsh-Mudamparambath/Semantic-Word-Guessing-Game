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

Two backends implement `SCORING_BACKENDS[name](secret, guess) -> int`:

  - "llm_judge": ask an Anthropic model to output a calibrated 0-100
    closeness score, anchored with few-shot examples. No embedding model
    download required. This is the default because the sandboxed dev
    environment here cannot reach huggingface.co to pull model weights.

  - "sentence_transformers": local embedding model + cosine similarity.
    Stubbed out below with the exact interface to fill in once you have
    unrestricted network access to download model weights. Swapping
    SCORING_BACKEND=sentence_transformers in .env is the only change
    needed elsewhere in the app — nothing else references the backend.

Do NOT use spelling/edit-distance similarity anywhere in this module.
"""

import functools
import os
import re

import anthropic

from app.config import get_settings

settings = get_settings()

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


def normalize(word: str) -> str:
    """Lowercase, trim, strip to letters only. Same normalization for
    secret words and guesses so 'Ocean', ' ocean ', 'OCEAN' all match."""
    word = word.strip().lower()
    word = re.sub(r"[^a-z]", "", word)
    return word


# ---------------------------------------------------------------------------
# LLM-judge backend
# ---------------------------------------------------------------------------

_CALIBRATION_EXAMPLES = """\
secret=ocean guess=computer -> 4
secret=ocean guess=mountain -> 17
secret=ocean guess=fish -> 62
secret=ocean guess=beach -> 82
secret=ocean guess=water -> 93
secret=ocean guess=sea -> 97
secret=football guess=soccer -> 91
secret=football guess=stadium -> 68
secret=football guess=banana -> 3
secret=doctor guess=hospital -> 71
secret=doctor guess=telescope -> 5
"""

_SYSTEM_PROMPT = f"""You score how semantically close a guessed word is to a secret word, \
for a word-guessing game. Output ONLY an integer 0-100. Base the score \
PURELY on meaning/semantic relatedness (shared concept, category, typical \
association, real-world connection) — NEVER on spelling, letters, length, \
or how the words sound. Two words can score very low even if they look or \
sound alike, and very high even if spelled completely differently.

Calibration anchors (secret, guess -> score) — match this scale closely:
{_CALIBRATION_EXAMPLES}
Respond with ONLY the integer, nothing else."""


@functools.lru_cache(maxsize=4096)
def _llm_judge_cached(secret_normalized: str, guess_normalized: str, model: str) -> int:
    client = _get_client()
    resp = client.messages.create(
        model=model,
        max_tokens=8,
        temperature=0,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"secret={secret_normalized} guess={guess_normalized} ->"}],
    )
    text = resp.content[0].text.strip()
    match = re.search(r"\d+", text)
    if not match:
        return 0
    return max(0, min(100, int(match.group())))


def score_llm_judge(secret_normalized: str, guess_normalized: str) -> int:
    return _llm_judge_cached(secret_normalized, guess_normalized, settings.anthropic_model)


# ---------------------------------------------------------------------------
# sentence-transformers backend (stub — fill in when model download is possible)
# ---------------------------------------------------------------------------

def score_sentence_transformers(secret_normalized: str, guess_normalized: str) -> int:
    """
    Reference implementation to complete once huggingface.co (or a mirror)
    is reachable from this environment:

        from sentence_transformers import SentenceTransformer
        import numpy as np

        _model = SentenceTransformer(settings.embedding_model)  # load once

        def score_sentence_transformers(secret_normalized, guess_normalized):
            vecs = _model.encode([secret_normalized, guess_normalized], normalize_embeddings=True)
            cosine = float(np.dot(vecs[0], vecs[1]))          # in [-1, 1]
            return calibrate(cosine)                          # -> [0, 100], see below

    `calibrate()` should be tuned against docs/game-mechanics.md examples
    (a simple linear remap of cosine's typical [0.2, 1.0] range into
    [0, 100] is a reasonable starting point; verify against the test
    dataset in scripts/ and tests/test_scoring.py before shipping).
    """
    raise NotImplementedError(
        "sentence_transformers backend requires downloading model weights; "
        "not available in this sandboxed environment. See docstring above."
    )


SCORING_BACKENDS = {
    "llm_judge": score_llm_judge,
    "sentence_transformers": score_sentence_transformers,
}


def calculate_score(secret_word: str, guess: str) -> int:
    """Public entry point: normalize, exact-match shortcut, then delegate
    to the configured scoring backend. Always returns an int in [0, 100]."""
    secret_normalized = normalize(secret_word)
    guess_normalized = normalize(guess)

    if not guess_normalized:
        return 0

    if guess_normalized == secret_normalized:
        return 100

    backend = SCORING_BACKENDS.get(settings.scoring_backend)
    if backend is None:
        raise ValueError(f"Unknown SCORING_BACKEND: {settings.scoring_backend}")

    score = backend(secret_normalized, guess_normalized)
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
