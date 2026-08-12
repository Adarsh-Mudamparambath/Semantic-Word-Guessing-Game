from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # --- Core ---
    environment: str = "development"
    secret_key: str = "change-me-in-production"
    frontend_url: str = "http://localhost:5173"
    cors_allowed_origins: list[str] = ["http://localhost:5173"]

    # --- Database ---
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/semantic_word_game"

    # --- Scoring engine ---
    # "llm_judge": call ANTHROPIC scoring model per guess (cached). Default —
    #   works without any local embedding model / GPU / model download.
    # "sentence_transformers": swap in a local embedding model later; see
    #   app/scoring.py for the interface a new backend must implement.
    scoring_backend: str = "llm_judge"
    anthropic_model: str = "claude-sonnet-4-6"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # used only if scoring_backend=sentence_transformers

    # --- Feedback thresholds (configurable, inclusive lower bound) ---
    feedback_thresholds: dict[int, str] = {
        0: "❄️ Very cold",
        20: "🧊 Cold",
        40: "🌱 Getting warmer",
        60: "🔥 Warm",
        80: "🔥🔥 Hot",
        90: "🔥🔥 Very hot",
        95: "🚨 Extremely close",
        100: "🎉 Correct",
    }

    # --- Rate limiting ---
    guess_rate_limit_per_minute: int = 30
    guess_min_length: int = 2
    guess_max_length: int = 40


    @property
    def allowed_origins(self) -> list[str]:
        if self.cors_allowed_origins:
            return self.cors_allowed_origins
        return [self.frontend_url]


@lru_cache
def get_settings() -> Settings:
    return Settings()
