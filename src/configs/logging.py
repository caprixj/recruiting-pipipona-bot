import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from src.configs.env_settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configures application-wide logging.

    Dependent on the Settings object passed from main.py. Sets up console logging,
    daily rotating file logging for all messages, and a separate error log file.

    Args:
        settings (Settings): Application settings containing LOG_LEVEL.
    """
    LOG_DIR = "logs"
    os.makedirs(LOG_DIR, exist_ok=True)

    # Formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    )
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Handlers

    # 1. Console (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(console_formatter)

    # 2. Daily Rotating File (All Logs)
    app_file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"), when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    app_file_handler.setLevel(settings.LOG_LEVEL)
    app_file_handler.setFormatter(file_formatter)

    # 3. Error File (Error and Critical Only)
    error_file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "error.log"), when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_formatter)

    # Root Logger Configuration
    logging.basicConfig(
        level=settings.LOG_LEVEL, handlers=[console_handler, app_file_handler, error_file_handler], force=True
    )

    # Silence noisy libraries
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
