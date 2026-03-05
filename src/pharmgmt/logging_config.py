"""Logging configuration — rotating file + console handlers."""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_dir: str, log_level: str = "INFO") -> None:
    """Configure application logging.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = logging.Formatter(fmt)

    # Root logger for pharmgmt
    root_logger = logging.getLogger("pharmgmt")
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler — rotating, 5MB max, 3 backups
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "pharmgmt.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler — minimal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    root_logger.info("Logging initialized — level=%s, dir=%s", log_level, log_dir)
