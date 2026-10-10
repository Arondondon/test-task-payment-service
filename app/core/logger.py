import logging
import sys

import structlog

from app.core.config import settings


def setup_logger(is_production: bool = True) -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
    ]

    if is_production:
        processors = shared_processors + [structlog.processors.JSONRenderer()]
        log_format = "%(message)s"
    else:
        processors = shared_processors + [structlog.dev.ConsoleRenderer()]
        log_format = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        format=log_format,
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
