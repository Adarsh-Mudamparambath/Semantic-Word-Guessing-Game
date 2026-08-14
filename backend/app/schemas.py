from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TodayGameResponse(BaseModel):
    game_id: str
    date: date
    mode: str = "daily"


class RevealResponse(BaseModel):
    game_id: str
    secret_word: str
    revealed_by_ad: bool = True


class GuessRequest(BaseModel):
    game_id: str
    guess: str = Field(..., min_length=1, max_length=64)

    @field_validator("guess")
    @classmethod
    def strip_guess(cls, v: str) -> str:
        return v.strip()


class GuessResponse(BaseModel):
    guess: str
    score: int
    feedback: str
    is_correct: bool
    guesses_remaining: Optional[int] = None


class HistoryEntry(BaseModel):
    guess: str
    score: int
    is_correct: bool


class HistoryResponse(BaseModel):
    game_id: str
    guesses: list[HistoryEntry]
    best_score: int
    solved: bool


class ErrorResponse(BaseModel):
    detail: str
