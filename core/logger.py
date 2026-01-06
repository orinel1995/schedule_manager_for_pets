import logging
from datetime import datetime


LOG_FILE = "log.csv"
DELIMITER = ";"


class CsvFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_time = (
            datetime.fromtimestamp(record.created)
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        level = record.levelname
        user = getattr(record, "user", "admin")
        message = record.getMessage()

        return (
            f"{log_time}{DELIMITER}{level}{DELIMITER}"
            f"{user}{DELIMITER}{message}"
        )


def get_logger(name: str = "project") -> logging.Logger:
    """
    Возвращает настроенный логгер.
    Один и тот же логгер используется во всём проекте.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(CsvFormatter())
        logger.addHandler(handler)

    return logger
