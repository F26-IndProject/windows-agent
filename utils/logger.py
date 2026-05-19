"""
utils/logger.py — Logging setup
"""

import logging
from pathlib import Path


def setup_logger(log_file: str = "logs/agent.log", level=logging.INFO) -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(threadName)s]: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("LISA-WinAgent")
