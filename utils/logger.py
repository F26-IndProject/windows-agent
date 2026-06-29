"""
utils/logger.py — Logging setup
"""
import logging
import logging.handlers
from pathlib import Path

LOG_WRITER_PORT = 19999

def setup_logger(log_file: str = "logs/agent.log", level=logging.INFO) -> logging.Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(threadName)s]: %(message)s",
        handlers=[
            logging.handlers.SocketHandler("127.0.0.1", LOG_WRITER_PORT),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("LISA-WinAgent")