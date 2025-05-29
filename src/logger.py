# src/logger.py
from pathlib import Path
import logging


def setup_logger(name: str = "app") -> logging.Logger:
    """Set up and return a configured logger."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"{name}.log"
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        file_handler = logging.FileHandler(
            log_file, encoding="utf-8", mode="a"
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
