import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    if name is None:
        name = __name__  # pragma: no cover
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# logger = get_logger(__name__)
