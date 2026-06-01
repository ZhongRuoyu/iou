import os
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE = Path(os.getenv("DATABASE", "iou.db"))
CURRENCY = os.getenv("CURRENCY", "USD")
REQUEST_EMAIL_HEADER = os.getenv("REQUEST_EMAIL_HEADER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
