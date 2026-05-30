import os
from pathlib import Path

DATABASE = Path(os.getenv("DATABASE", "iou.db"))
CURRENCY = os.getenv("CURRENCY", "USD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
