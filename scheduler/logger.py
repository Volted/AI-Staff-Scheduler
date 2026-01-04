import os
import sys
from loguru import logger


def setup_logger(
        enable_file_logging: bool = False,
        log_level: str = "INFO"
) -> None:
    """
    Configure application-wide logging.

    Args:
        enable_file_logging: Whether to write logs to files in logs/ directory
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove default handler
    logger.remove()

    # Add console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level
    )

    # Add a file handler if enabled
    if enable_file_logging:
        # Ensure the logs directory exists
        os.makedirs("logs", exist_ok=True)

        logger.add(
            "logs/scheduler_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level="DEBUG",  # Always capture DEBUG in files for troubleshooting
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
        )
        logger.info("File logging enabled - writing to logs/ directory")
    else:
        logger.info("File logging disabled - console output only")