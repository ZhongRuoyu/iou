import os
from pathlib import Path

DATABASE = Path(os.getenv("DATABASE", "iou.db"))
CURRENCY = os.getenv("CURRENCY", "USD")
