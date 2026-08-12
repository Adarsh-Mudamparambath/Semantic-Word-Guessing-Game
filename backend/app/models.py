import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_word: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyGame(Base):
    __tablename__ = "daily_games"
    __table_args__ = (UniqueConstraint("game_date", name="uq_daily_games_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    secret_word_id: Mapped[int] = mapped_column(ForeignKey("words.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    secret_word: Mapped["Word"] = relationship()


class PlayerSession(Base):
    __tablename__ = "player_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Guess(Base):
    __tablename__ = "guesses"
    __table_args__ = (
        Index("ix_guesses_game_session", "daily_game_id", "session_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    daily_game_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_games.id"), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player_sessions.id"), nullable=False)
    guess: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_guess: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ScoreCache(Base):
    """Cache of (secret_word, guess) -> score so repeated/popular guesses
    across all players never re-hit the scoring backend."""

    __tablename__ = "score_cache"
    __table_args__ = (UniqueConstraint("secret_normalized", "guess_normalized", name="uq_score_cache_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    secret_normalized: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    guess_normalized: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
