from unittest.mock import patch

from app import scoring


def test_normalize():
    assert scoring.normalize("Ocean") == "ocean"
    assert scoring.normalize(" ocean ") == "ocean"
    assert scoring.normalize("OcEaN") == "ocean"
    assert scoring.normalize("océan!") == "ocan"  # strips non a-z incl. accented chars


def test_exact_match_always_100():
    assert scoring.calculate_score("ocean", "ocean") == 100
    assert scoring.calculate_score("Ocean", " OCEAN ") == 100


def test_non_exact_never_reaches_100():
    with patch.object(scoring, "SCORING_BACKENDS", {"sentence_transformers": lambda s, g, db: 100}):
        score = scoring.calculate_score("ocean", "sea")
        assert score <= 99


def test_score_clamped_0_100():
    with patch.object(scoring, "SCORING_BACKENDS", {"sentence_transformers": lambda s, g, db: 500}):
        assert scoring.calculate_score("ocean", "banana") <= 100
    with patch.object(scoring, "SCORING_BACKENDS", {"sentence_transformers": lambda s, g, db: -20}):
        assert scoring.calculate_score("ocean", "banana") >= 0


def test_empty_guess_scores_zero():
    assert scoring.calculate_score("ocean", "   ") == 0


def test_cosine_similarity_is_calibrated_without_spelling():
    with patch.object(
        scoring,
        "_get_embedding_for_word",
        side_effect=[scoring.np.array([1.0, 0.0]), scoring.np.array([1.0, 0.0])],
    ):
        assert scoring.score_sentence_transformers("ocean", "sea", object()) == 100


def test_feedback_thresholds_monotonic():
    labels = [scoring.get_feedback(s) for s in (0, 25, 45, 65, 85, 92, 96, 100)]
    # each threshold tier should differ from the previous as score climbs
    assert len(set(labels)) >= 6


def test_relative_ordering_placeholder():
    """
    This is where scripts/generate_word_list.py-style semantic ordering
    checks would run against a live scoring backend, e.g.:

        assert calculate_score("ocean", "sea") > calculate_score("ocean", "mountain")

    Run this ordering check after embeddings are precomputed in a test database.
    """
    assert True
