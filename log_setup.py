import logging
from datetime import date

from config import LOG_DIR


def setup_logging() -> logging.Logger:
    log_file = LOG_DIR / f"analysis_{date.today().isoformat()}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)

