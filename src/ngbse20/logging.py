import logging
import os

_LEVEL = os.getenv("NGBSE_LOG_LEVEL", "INFO").upper()
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def get_logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or "ngbse20")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(_LEVEL)
        logger.propagate = False
    return logger
