import logging
import os
from logging.handlers import TimedRotatingFileHandler

from core.settings import core_settings


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logger(name: str = "app") -> logging.Logger:
    os.makedirs(core_settings.LOG_DIR, exist_ok=True)
    log_path = os.path.join(core_settings.LOG_DIR, core_settings.LOG_FILE)

    logger = logging.getLogger(name)
    logger.setLevel(core_settings.LOG_LEVEL)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
