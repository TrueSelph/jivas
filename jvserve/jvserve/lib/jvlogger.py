"""JVLogger module for setting up logging with colored console and JSON file handlers."""

import json
import logging
import os
from logging.handlers import RotatingFileHandler


class JVLogger:
    """JVLogger class for setting up logging with colored console and JSON file handlers."""

    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
        "RESET": "\033[0m",  # Reset color
    }

    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    @staticmethod
    def setup_logging(
        log_file: str = "/tmp/jac_cloud_logs/jivas.log", level: str = "INFO"
    ) -> None:
        """Set up logging with colored console and JSON file handlers.

        @param log_file: Path to the log file.
        @param level: Logging level.
        """
        # Clear existing handlers to prevent duplicate logs
        root_logger = logging.getLogger()
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # Console handler with colored formatter
        console_formatter = JVLogger.ColoredConsoleFormatter(
            "%(levelname)s:     %(message)s"
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)

        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))

        # File handler with JSON formatter
        json_file_handler = logging.FileHandler(log_file)
        json_file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        json_file_handler.setFormatter(JVLogger.JSONFormatter())

        # Root logger configuration
        loglevel = JVLogger.LEVELS.get(level.upper(), logging.INFO)
        root_logger.setLevel(loglevel)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(json_file_handler)

    class ColoredConsoleFormatter(logging.Formatter):
        """Formatter for colored console logging."""

        def format(self, record: logging.LogRecord) -> str:
            """Format the log record with colors for console output.

            @param record: Log record to format.
            @return: Formatted log record string.
            """
            # Only applies colors to console levelname
            levelname = record.levelname
            color = JVLogger.COLORS.get(levelname, "")
            reset = JVLogger.COLORS["RESET"]
            original_levelname = record.levelname
            record.levelname = f"{color}{levelname}{reset}"
            # Format message and then restore original levelname to avoid altering the file logs
            formatted_message = super().format(record)
            record.levelname = original_levelname
            return formatted_message

    class JSONFormatter(logging.Formatter):
        """Formatter for JSON file logging."""

        def format(self, record: logging.LogRecord) -> str:
            """Format the log record as a JSON string.

            @param record: Log record to format.
            @return: JSON string of the log record.
            """
            # Create a dictionary to store log record information
            log_record = {
                "asctime": self.formatTime(record, self.datefmt),
                "name": record.name,
                "levelname": record.levelname,
                "message": record.getMessage(),
                "filename": record.filename,  # Name of the file where the log was created
                "funcName": record.funcName,  # Name of the function where the log was created
                "lineno": record.lineno,  # Line number where the log was created
                "module": record.module,  # Module name where the log was created
                "thread": record.threadName,  # Thread name
            }
            # Convert the log record dictionary to a JSON string
            return json.dumps(log_record)
