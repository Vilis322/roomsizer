"""Logging configuration for the RoomSizer application.

This module configures logging with both console and file handlers, allowing
for INFO-level output to the console and DEBUG-level output to a log file.
Configuration can be controlled via environment variables or function arguments.
"""

import logging
import logging.handlers
import os
import sys
import time
from pathlib import Path
from typing import Any


def configure_logging(
    console_level: int | None = None,
    file_level: int | None = None,
    log_dir: str | None = None,
    log_file: str | None = None,
    use_utc: bool = False,
    force_reconfigure: bool = False,
) -> dict[str, Any]:
    """Configure logging for the application.

    Sets up two handlers:
    - Console handler: outputs INFO and above to stderr
    - File handler: outputs DEBUG and above to a rotating log file

    Configuration precedence (highest to lowest):
    1. Function arguments (if not None)
    2. Environment variables (LOG_LEVEL_CONSOLE, LOG_LEVEL_FILE, LOG_DIR, LOG_FILE)
    3. Default values

    Args:
        console_level: Minimum level for console output (default: INFO).
        file_level: Minimum level for file output (default: DEBUG).
        log_dir: Directory for log files (default: "logs").
        log_file: Name of the log file (default: "app.log").
        use_utc: Use UTC timestamps in logs (default: False).
        force_reconfigure: Force reconfiguration even if already configured.

    Returns:
        Dictionary with configuration details:
        - console_level: Level name for console
        - file_level: Level name for file
        - log_file: Full path to log file
        - reconfigured: Whether configuration was applied (vs. skipped)

    Environment Variables:
        LOG_LEVEL_CONSOLE: Console log level (e.g., "INFO", "DEBUG")
        LOG_LEVEL_FILE: File log level (e.g., "DEBUG", "WARNING")
        LOG_DIR: Directory for log files
        LOG_FILE: Log file name
    """
    # Check if already configured (idempotent guard)
    root_logger = logging.getLogger()
    if root_logger.handlers and not force_reconfigure:
        return {
            "console_level": "N/A",
            "file_level": "N/A",
            "log_file": "N/A",
            "reconfigured": False,
        }

    # Resolve configuration from args -> env -> defaults
    def _get_log_level(name: str, default: int) -> int:
        """Get log level from environment or use default."""
        env_value = os.environ.get(name)
        if env_value:
            try:
                return getattr(logging, env_value.upper())
            except AttributeError:
                pass  # Fall through to default
        return default

    resolved_console_level = (
        console_level
        if console_level is not None
        else _get_log_level("LOG_LEVEL_CONSOLE", logging.INFO)
    )
    resolved_file_level = (
        file_level
        if file_level is not None
        else _get_log_level("LOG_LEVEL_FILE", logging.DEBUG)
    )
    resolved_log_dir = (
        log_dir if log_dir is not None else os.environ.get("LOG_DIR", "logs")
    )
    resolved_log_file = (
        log_file if log_file is not None else os.environ.get("LOG_FILE", "app.log")
    )

    # Create logs directory if it doesn't exist
    log_path = Path(resolved_log_dir)
    log_path.mkdir(exist_ok=True)

    # Configure root logger
    root_logger.setLevel(logging.DEBUG)  # Capture all levels

    # Remove existing handlers if force reconfiguring
    if force_reconfigure:
        root_logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(fmt="%(levelname)s: %(message)s")

    # Set UTC timestamps if requested
    if use_utc:
        detailed_formatter.converter = time.gmtime
        simple_formatter.converter = time.gmtime

    # Console handler (INFO and above by default)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(resolved_console_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # File handler (DEBUG and above by default) with rotation
    full_log_path = log_path / resolved_log_file
    file_handler = logging.handlers.RotatingFileHandler(
        filename=full_log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(resolved_file_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Capture warnings into logging system
    logging.captureWarnings(True)

    # Quiet noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # Log configuration success
    logging.info("[Logging] Configured with console and file handlers")
    logging.debug(
        "[Logging] Console level: %s, File level: %s, Log file: %s",
        logging.getLevelName(resolved_console_level),
        logging.getLevelName(resolved_file_level),
        full_log_path,
    )

    return {
        "console_level": logging.getLevelName(resolved_console_level),
        "file_level": logging.getLevelName(resolved_file_level),
        "log_file": str(full_log_path),
        "reconfigured": True,
    }
