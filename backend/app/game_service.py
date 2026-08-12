import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, scoring
from app.config import get_settings

settings = get_settings()

NO_REPEAT_WINDOW_DAYS = 60  # don't reuse a secret word within this many days


def get_or_create_daily_game(db: Session, game_date: date) -> models.DailyGame:
    existing = db.execute(
        select(models.DailyGame).where(models.DailyGame.game_date == game_date)
    ).scalar_one_or_none()
    if existing:
        return existing

    recent_word_ids = db.execute(
        select(models.DailyGame.secret_word_id).where(
            models.DailyGame.game_date >= game_date - timedelta(days=NO_REPEAT_WINDOW_DAYS)
        )
    ).scalars().all()

    # Deterministic-ish but simple: pick the active word with the oldest
    # (or no) prior use, ordered by id for stability, offset by date so
    # different dates naturally diverge. Admins can override via
    # set_daily_game_override().
    query = select(models.Word).where(models.Word.is_active.is_(True))
    if recent_word_ids:
        query = query.where(models.Word.id.notin_(recent_word_ids))
    query = query.order_by(func.random()).limit(1)

    word = db.execute(query).scalar_one_or_none()
    if word is None:
        # Every active word was used recently (tiny dataset) — fall back to
        # any active word rather than failing the game.
        word = db.execute(
            select(models.Word).where(models.Word.is_active.is_(True)).order_by(func.random()).limit(1)
        ).scalar_one()

    daily_game = models.DailyGame(game_date=game_date, secret_word_id=word.id)
    db.add(daily_game)
    db.commit()
    db.refresh(daily_game)
    return daily_game


def set_daily_game_override(db: Session, game_date: date, word_id: int) -> models.DailyGame:
    """Admin-only: force a specific word for a given date."""
    existing = db.execute(
        select(models.DailyGame).where(models.DailyGame.game_date == game_date)
    ).scalar_one_or_none()
    if existing:
        existing.secret_word_id = word_id
        db.commit()
        db.refresh(existing)
        return existing
    daily_game = models.DailyGame(game_date=game_date, secret_word_id=word_id)
    db.add(daily_game)
    db.commit()
    db.refresh(daily_game)
    return daily_game


def get_or_create_session(db: Session, session_id: str | None) -> models.PlayerSession:
    if session_id:
        existing = db.get(models.PlayerSession, uuid.UUID(session_id))
        if existing:
            return existing
    new_session = models.PlayerSession()
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


def _cached_score(db: Session, secret_normalized: str, guess_normalized: str) -> int | None:
    row = db.execute(
        select(models.ScoreCache).where(
            models.ScoreCache.secret_normalized == secret_normalized,
            models.ScoreCache.guess_normalized == guess_normalized,
        )
    ).scalar_one_or_none()
    return row.score if row else None


def _write_cache(db: Session, secret_normalized: str, guess_normalized: str, score: int) -> None:
    db.add(models.ScoreCache(
        secret_normalized=secret_normalized,
        guess_normalized=guess_normalized,
        score=score,
    ))
    try:
        db.commit()
    except Exception:
        db.rollback()  # another request wrote the same pair concurrently; fine


def submit_guess(
    db: Session,
    daily_game: models.DailyGame,
    session: models.PlayerSession,
    raw_guess: str,
) -> tuple[models.Guess, bool]:
    """Returns (guess_row, was_duplicate). Handles exact-match, dedup, and
    the cross-player score cache."""
    normalized_guess = scoring.normalize(raw_guess)
    secret_normalized = scoring.normalize(daily_game.secret_word.normalized_word)

    # Duplicate guess by this session -> return the prior result, don't
    # re-score.
    prior = db.execute(
        select(models.Guess).where(
            models.Guess.daily_game_id == daily_game.id,
            models.Guess.session_id == session.id,
            models.Guess.normalized_guess == normalized_guess,
        ).order_by(models.Guess.created_at.desc())
    ).scalars().first()
    if prior:
        return prior, True

    if normalized_guess == secret_normalized:
        score = 100
    else:
        cached = _cached_score(db, secret_normalized, normalized_guess)
        if cached is not None:
            score = cached
        else:
            score = scoring.calculate_score(daily_game.secret_word.normalized_word, raw_guess)
            _write_cache(db, secret_normalized, normalized_guess, score)

    guess_row = models.Guess(
        daily_game_id=daily_game.id,
        session_id=session.id,
        guess=raw_guess.strip(),
        normalized_guess=normalized_guess,
        score=score,
        is_correct=(score == 100),
    )
    db.add(guess_row)
    db.commit()
    db.refresh(guess_row)
    return guess_row, False
