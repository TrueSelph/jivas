"""Tests for JVLogger class"""

import json
import logging

from pytest_mock import MockerFixture

from jvserve.lib.jvlogger import JVLogger


class TestJVLogger:
    """Test JVLogger class"""

    def test_setup_logging_with_defaults(self, mocker: MockerFixture) -> None:
        """Test setup_logging with default parameters."""
        # Mock file handler and root logger
        mock_rotating_handler = mocker.patch("jvserve.lib.jvlogger.RotatingFileHandler")
        mocker.patch("logging.StreamHandler")
        mock_root_logger = mocker.patch("logging.getLogger")
        mock_logger = mocker.MagicMock()
        mock_root_logger.return_value = mock_logger

        # Call setup_logging with defaults
        JVLogger.setup_logging()

        # Verify root logger was configured correctly
        mock_root_logger.assert_called_once()
        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        assert mock_logger.addHandler.call_count == 2

        # Verify file handler was created with default path
        mock_rotating_handler.assert_called_once_with(
            "/tmp/jac_cloud_logs/jivas.log", maxBytes=5242880, backupCount=5
        )

    def test_invalid_log_level_defaults_to_info(self, mocker: MockerFixture) -> None:
        """Test that an invalid log level defaults to INFO."""
        # Mock root logger
        mock_root_logger = mocker.patch("logging.getLogger")
        mock_logger = mocker.MagicMock()
        mock_root_logger.return_value = mock_logger

        # Call setup_logging with invalid level
        JVLogger.setup_logging(level="INVALID_LEVEL")

        # Verify INFO level was used as default
        mock_logger.setLevel.assert_called_once_with(logging.INFO)

    def test_colored_console_formatter_format(self, mocker: MockerFixture) -> None:
        """Test the format method of ColoredConsoleFormatter."""
        # Mock a log record
        mock_record = mocker.MagicMock()
        mock_record.levelname = "INFO"
        mock_record.getMessage.return_value = "Test message"

        # Create an instance of ColoredConsoleFormatter
        formatter = JVLogger.ColoredConsoleFormatter("%(levelname)s: %(message)s")

        # Format the mock record
        formatted_message = formatter.format(mock_record)

        # Verify the formatted message contains the colored levelname
        expected_color = JVLogger.COLORS["INFO"]
        reset_color = JVLogger.COLORS["RESET"]
        assert formatted_message.startswith(
            f"{expected_color}INFO{reset_color}: Test message"
        )

    def test_json_formatter_output(self, mocker: MockerFixture) -> None:
        """Test the output of JSONFormatter."""
        # Create a mock log record
        mock_record = mocker.MagicMock()
        mock_record.levelname = "INFO"
        mock_record.getMessage.return_value = "Test message"
        mock_record.name = "test_logger"
        mock_record.filename = "test_file.py"
        mock_record.funcName = "test_function"
        mock_record.lineno = 10
        mock_record.module = "test_module"
        mock_record.threadName = "MainThread"

        # Mock the formatTime method to return a fixed time
        mocker.patch.object(
            JVLogger.JSONFormatter, "formatTime", return_value="2023-10-01 12:00:00"
        )

        # Initialize JSONFormatter and format the mock record
        json_formatter = JVLogger.JSONFormatter()
        formatted_output = json_formatter.format(mock_record)

        # Expected JSON output
        expected_output = json.dumps(
            {
                "asctime": "2023-10-01 12:00:00",
                "name": "test_logger",
                "levelname": "INFO",
                "message": "Test message",
                "filename": "test_file.py",
                "funcName": "test_function",
                "lineno": 10,
                "module": "test_module",
                "thread": "MainThread",
            }
        )

        # Assert the formatted output matches the expected JSON string
        assert formatted_output == expected_output
