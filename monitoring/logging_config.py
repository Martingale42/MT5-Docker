"""
Structured JSON Logging Configuration for MT5-Docker

Provides consistent JSON-formatted logging across the application for
easy parsing by log aggregation systems (ELK, Loki, etc.).

Usage:
    from monitoring.logging_config import get_logger

    logger = get_logger(__name__)
    logger.info("Processing trade", extra={"symbol": "EURUSD", "volume": 0.1})
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON-formatted log records.

    Each log record includes:
    - timestamp (ISO 8601)
    - level (INFO, WARNING, ERROR, etc.)
    - logger (logger name)
    - message (log message)
    - Additional context fields from 'extra' parameter
    """

    def __init__(
        self,
        service_name: str = "mt5-docker",
        environment: str = "production",
        include_traceback: bool = True
    ):
        """
        Initialize JSON formatter.

        Args:
            service_name: Name of the service for log tagging
            environment: Environment name (dev, staging, production)
            include_traceback: Include full traceback for exceptions
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_traceback = include_traceback

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }

        # Add standard fields
        if record.levelno >= logging.WARNING:
            log_data["severity"] = "high" if record.levelno >= logging.ERROR else "medium"

        # Add source location
        log_data["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }

        # Add process/thread info
        log_data["process"] = {
            "pid": record.process,
            "thread": record.thread,
            "thread_name": record.threadName
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1])
            }

            if self.include_traceback:
                log_data["exception"]["traceback"] = traceback.format_exception(
                    *record.exc_info
                )

        # Add extra context fields (from logger.info(..., extra={...}))
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Handle other custom attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "lineno", "module", "msecs", "message", "pathname",
                "process", "processName", "relativeCreated", "thread", "threadName",
                "exc_info", "exc_text", "stack_info", "extra_fields"
            ]:
                # Skip private attributes
                if not key.startswith("_"):
                    log_data[key] = value

        return json.dumps(log_data, default=str, ensure_ascii=False)


class StructuredLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds structured context to log records.

    Allows adding persistent context fields that will be included
    in all log messages from this logger instance.
    """

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        """
        Initialize structured logger.

        Args:
            logger: Base logger instance
            extra: Default context fields for all log messages
        """
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message to add context fields.

        Args:
            msg: Log message
            kwargs: Keyword arguments from logging call

        Returns:
            Tuple of (message, kwargs) with processed context
        """
        # Merge default extra fields with call-specific extra fields
        extra_fields = {**self.extra}

        if "extra" in kwargs:
            extra_fields.update(kwargs["extra"])

        # Store in record for JSON formatter
        if extra_fields:
            kwargs["extra"] = {"extra_fields": extra_fields}

        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    service_name: str = "mt5-docker",
    environment: str = "production",
    log_file: Optional[str] = None,
    console_output: bool = True,
    json_format: bool = True
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Service name for log tagging
        environment: Environment name
        log_file: Optional file path for log output
        console_output: Enable console output
        json_format: Use JSON formatter (True) or simple text (False)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create formatter
    if json_format:
        formatter = JSONFormatter(
            service_name=service_name,
            environment=environment
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None
) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)
        context: Default context fields for all log messages

    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(name)
    return StructuredLogger(logger, context)


# Example usage and helper functions
def log_zmq_request(logger: StructuredLogger, action: str, duration: float, success: bool):
    """
    Helper to log ZMQ requests in a consistent format.

    Args:
        logger: Logger instance
        action: ZMQ action type
        duration: Request duration in seconds
        success: Whether request succeeded
    """
    logger.info(
        f"ZMQ request completed: {action}",
        extra={
            "component": "zmq",
            "action": action,
            "duration_seconds": duration,
            "success": success
        }
    )


def log_trade_event(
    logger: StructuredLogger,
    event_type: str,
    symbol: str,
    volume: float,
    price: Optional[float] = None,
    ticket: Optional[int] = None
):
    """
    Helper to log trading events in a consistent format.

    Args:
        logger: Logger instance
        event_type: Event type (open, close, modify)
        symbol: Trading symbol
        volume: Trade volume
        price: Trade price
        ticket: Order ticket number
    """
    extra_data = {
        "component": "trading",
        "event_type": event_type,
        "symbol": symbol,
        "volume": volume
    }

    if price is not None:
        extra_data["price"] = price
    if ticket is not None:
        extra_data["ticket"] = ticket

    logger.info(
        f"Trade event: {event_type} {volume} {symbol}",
        extra=extra_data
    )


# Configure default logging on import
# Can be overridden by calling setup_logging() explicitly
if __name__ != "__main__":
    setup_logging(
        level="INFO",
        console_output=True,
        json_format=True
    )
