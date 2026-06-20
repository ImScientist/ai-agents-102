"""
logging_config.py
Central logging configuration for the Movie Agent.

Call setup_logging() once at the entry point (main.py) before importing
any application modules. Every other module then simply does:

    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the whole application.

    Output format:
        2026-06-18 12:34:56 | INFO     | agent_movie.tools | message here

    Args:
        level: Minimum log level to emit (default: logging.INFO).
               Pass logging.DEBUG to see tool-call tracing.
    """
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(level)

    # Replace any previously registered handlers to avoid duplicate output
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

