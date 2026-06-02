import os
from pathlib import Path
from typing import TypedDict


class AppConfigItems(TypedDict):
  LOG_LEVEL: str
  DATABASE: Path
  CURRENCY: str
  REQUEST_EMAIL_HEADER: str | None
  TELEGRAM_BOT_TOKEN: str | None
  TELEGRAM_CHAT_ID: str | None


def load_env_config() -> AppConfigItems:
  """Load application config values from environment variables."""
  return {
    "LOG_LEVEL": os.getenv("OWE_LOG_LEVEL", "INFO").upper(),
    "DATABASE": Path(os.getenv("OWE_DATABASE", "owe.db")),
    "CURRENCY": os.getenv("OWE_CURRENCY", "USD"),
    "REQUEST_EMAIL_HEADER": os.getenv("OWE_REQUEST_EMAIL_HEADER"),
    "TELEGRAM_BOT_TOKEN": os.getenv("OWE_TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_CHAT_ID": os.getenv("OWE_TELEGRAM_CHAT_ID"),
  }
