from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during static checks
    load_dotenv = None


if load_dotenv:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    document_db_path: Path = Path(os.getenv("DOCUMENT_DB_PATH", "data/documents.sqlite3"))
    scheduler_jobs_path: Path = Path(os.getenv("SCHEDULER_JOBS_PATH", "scheduler_jobs.json"))
    scheduler_state_path: Path = Path(os.getenv("SCHEDULER_STATE_PATH", "data/scheduler_state.json"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    ops_consumer_key: str | None = os.getenv("OPS_CONSUMER_KEY") or None
    ops_consumer_secret: str | None = os.getenv("OPS_CONSUMER_SECRET") or None
    eu_funding_api_url: str = os.getenv(
        "EU_FUNDING_API_URL",
        "https://api.tech.ec.europa.eu/search-api/prod/rest/search",
    )
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    user_agent: str = os.getenv(
        "NEXUSBRIDGE_USER_AGENT",
        "NexusBridge/0.1 data-prep; contact=local-development",
    )
    default_refresh_hours: int = int(os.getenv("DEFAULT_REFRESH_HOURS", "24"))


settings = Settings()
