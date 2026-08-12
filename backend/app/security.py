import time
from collections import defaultdict, deque

from fastapi import Cookie, HTTPException, Response, status

from app.config import get_settings

settings = get_settings()

SESSION_COOKIE_NAME = "swg_session"

# Simple in-memory sliding-window rate limiter, keyed by session id.
# Fine for a single-process MVP; swap for Redis if scaling to multiple
# backend workers.
_request_log: dict[str, deque] = defaultdict(deque)


def rate_limit(session_key: str) -> None:
    now = time.time()
    window = 60.0
    log = _request_log[session_key]
    while log and now - log[0] > window:
        log.popleft()
    if len(log) >= settings.guess_rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many guesses. Slow down a little and try again.",
        )
    log.append(now)


def read_session_cookie(swg_session: str | None = Cookie(default=None)) -> str | None:
    return swg_session


def write_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=(settings.environment == "production"),
        max_age=60 * 60 * 24 * 365,
    )
