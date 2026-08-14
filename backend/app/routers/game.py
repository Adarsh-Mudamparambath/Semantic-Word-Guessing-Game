import uuid
from datetime import date, timedelta, timezone, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import game_service, models, scoring
from app.config import get_settings
from app.database import get_db
from app.schemas import (
    GuessRequest,
    GuessResponse,
    HistoryEntry,
    HistoryResponse,
    RevealResponse,
    TodayGameResponse,
)
from app.security import read_session_cookie, rate_limit, write_session_cookie

router = APIRouter(prefix="/api/game", tags=["game"])
settings = get_settings()


def _today() -> date:
    return datetime.now(timezone.utc).date()


@router.get("/today", response_model=TodayGameResponse)
def get_today(
    response: Response,
    db: Session = Depends(get_db),
    session_id: str | None = Depends(read_session_cookie),
):
    daily_game = game_service.get_or_create_daily_game(db, _today())
    session = game_service.get_or_create_session(db, session_id)
    write_session_cookie(response, str(session.id))
    # Secret word is intentionally NEVER included in this response.
    return TodayGameResponse(game_id=str(daily_game.id), date=daily_game.game_date)


@router.get("/reveal", response_model=RevealResponse)
def reveal_secret_word(
    game_id: str,
    db: Session = Depends(get_db),
    session_id: str | None = Depends(read_session_cookie),
):
    try:
        game_uuid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")

    daily_game = db.get(models.DailyGame, game_uuid)
    random_round = None if daily_game else db.get(models.RandomRound, game_uuid)
    if daily_game is None and random_round is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")
    if random_round is not None and str(random_round.session_id) != session_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")

    active_game = daily_game or random_round

    return RevealResponse(
        game_id=str(active_game.id),
        secret_word=active_game.secret_word.normalized_word,
        revealed_by_ad=True,
    )


@router.post("/new-round", response_model=TodayGameResponse)
def start_next_round(
    response: Response,
    payload: dict | None = None,
    db: Session = Depends(get_db),
    session_id: str | None = Depends(read_session_cookie),
):
    session = game_service.get_or_create_session(db, session_id)
    write_session_cookie(response, str(session.id))
    excluded_word_ids: set[int] = set()
    previous_game_id = (payload or {}).get("game_id")
    if previous_game_id:
        try:
            previous_game_uuid = uuid.UUID(previous_game_id)
        except ValueError:
            previous_game_uuid = None
        if previous_game_uuid:
            previous_daily = db.get(models.DailyGame, previous_game_uuid)
            previous_random = None if previous_daily else db.get(models.RandomRound, previous_game_uuid)
            if previous_daily:
                excluded_word_ids.add(previous_daily.secret_word_id)
            elif previous_random and previous_random.session_id == session.id:
                excluded_word_ids.add(previous_random.secret_word_id)

    random_round = game_service.create_random_round(db, session, excluded_word_ids)
    return TodayGameResponse(game_id=str(random_round.id), date=_today(), mode="random")


@router.post("/guess", response_model=GuessResponse)
def post_guess(
    payload: GuessRequest,
    response: Response,
    db: Session = Depends(get_db),
    session_id: str | None = Depends(read_session_cookie),
):
    session = game_service.get_or_create_session(db, session_id)
    write_session_cookie(response, str(session.id))
    rate_limit(str(session.id))

    normalized = scoring.normalize(payload.guess)
    if len(normalized) < settings.guess_min_length or len(normalized) > settings.guess_max_length:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Please enter a valid word.")

    try:
        game_uuid = uuid.UUID(payload.game_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")

    daily_game = db.get(models.DailyGame, game_uuid)
    random_round = None if daily_game else db.get(models.RandomRound, game_uuid)
    if daily_game is None and (random_round is None or random_round.session_id != session.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found.")

    # If already solved by this session, don't leak more info — just replay
    # the winning result.
    guess_model = models.Guess if daily_game else models.RandomGuess
    game_column = guess_model.daily_game_id if daily_game else guess_model.random_round_id
    active_game = daily_game or random_round
    already_won = db.execute(
        select(guess_model).where(
            game_column == active_game.id,
            guess_model.session_id == session.id,
            guess_model.is_correct.is_(True),
        )
    ).scalar_one_or_none()
    if already_won:
        return GuessResponse(
            guess=already_won.guess,
            score=already_won.score,
            feedback=scoring.get_feedback(already_won.score),
            is_correct=True,
        )

    if daily_game:
        guess_row, _was_duplicate = game_service.submit_guess(db, daily_game, session, payload.guess)
    else:
        guess_row, _was_duplicate = game_service.submit_random_guess(db, random_round, session, payload.guess)

    return GuessResponse(
        guess=guess_row.guess,
        score=guess_row.score,
        feedback=scoring.get_feedback(guess_row.score),
        is_correct=guess_row.is_correct,
    )


@router.get("/history", response_model=HistoryResponse)
def get_history(
    game_id: str,
    db: Session = Depends(get_db),
    session_id: str | None = Depends(read_session_cookie),
):
    if not session_id:
        return HistoryResponse(game_id=game_id, guesses=[], best_score=0, solved=False)

    try:
        game_uuid = uuid.UUID(game_id)
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return HistoryResponse(game_id=game_id, guesses=[], best_score=0, solved=False)

    daily_game = db.get(models.DailyGame, game_uuid)
    if daily_game:
        query = select(models.Guess).where(
            models.Guess.daily_game_id == game_uuid, models.Guess.session_id == session_uuid
        ).order_by(models.Guess.created_at.asc())
    else:
        random_round = db.get(models.RandomRound, game_uuid)
        if random_round is None or random_round.session_id != session_uuid:
            return HistoryResponse(game_id=game_id, guesses=[], best_score=0, solved=False)
        query = select(models.RandomGuess).where(
            models.RandomGuess.random_round_id == game_uuid, models.RandomGuess.session_id == session_uuid
        ).order_by(models.RandomGuess.created_at.asc())
    rows = db.execute(query).scalars().all()

    best = max((r.score for r in rows), default=0)
    solved = any(r.is_correct for r in rows)

    return HistoryResponse(
        game_id=game_id,
        guesses=[HistoryEntry(guess=r.guess, score=r.score, is_correct=r.is_correct) for r in rows],
        best_score=best,
        solved=solved,
    )
