from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def load_project_env() -> Path:
    """Load environment variables from the project root .env file."""
    load_dotenv(ENV_FILE)
    return ENV_FILE


def get_env(name: str, default: str | None = None) -> str | None:
    load_project_env()
    return os.getenv(name, default)
