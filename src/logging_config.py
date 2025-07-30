"""
Logging configuration for CEAF Farmácia application.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    log_format: str = None,
    enable_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Set up comprehensive logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_format: Custom log format (optional)
        enable_console: Whether to enable console logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Default log format
    if not log_format:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
        )
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file or 'None'}")
    
    return root_logger


def setup_error_handling():
    """Set up global error handling for uncaught exceptions."""
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions by logging them."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = logging.getLogger("uncaught_exception")
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    # Set the exception handler
    sys.excepthook = handle_exception


class RequestFormatter(logging.Formatter):
    """Custom formatter for Flask request logging."""
    
    def format(self, record):
        # Try to get Flask request context
        try:
            from flask import request, g
            
            # Add request information to log record
            record.url = getattr(request, 'url', 'N/A')
            record.method = getattr(request, 'method', 'N/A')
            record.ip = getattr(request, 'remote_addr', 'N/A')
            record.user_agent = getattr(request, 'user_agent', 'N/A')
            
            # Add custom attributes if they exist
            record.request_id = getattr(g, 'request_id', 'N/A')
            
        except (RuntimeError, ImportError):
            # Outside of Flask context or Flask not available
            record.url = 'N/A'
            record.method = 'N/A'
            record.ip = 'N/A'
            record.user_agent = 'N/A'
            record.request_id = 'N/A'
        
        return super().format(record)


def setup_flask_logging(app):
    """Set up logging specifically for Flask application."""
    
    # Custom request format
    request_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(request_id)s] %(method)s %(url)s - %(ip)s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )
    
    # Create request formatter
    request_formatter = RequestFormatter(request_format)
    
    # Set up Flask's logger
    app.logger.handlers.clear()
    
    # Console handler for Flask
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(request_formatter)
    app.logger.addHandler(console_handler)
    
    # File handler for Flask
    log_file = os.getenv('LOG_FILE', 'logs/flask.log')
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(request_formatter)
        app.logger.addHandler(file_handler)
    
    # Set Flask log level
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Add request ID middleware
    @app.before_request
    def add_request_id():
        import uuid
        from flask import g
        g.request_id = str(uuid.uuid4())[:8]
    
    # Log request start
    @app.before_request
    def log_request_start():
        from flask import request, g
        app.logger.info(f"Request started: {request.method} {request.url}")
    
    # Log request end
    @app.after_request
    def log_request_end(response):
        from flask import request, g
        app.logger.info(
            f"Request completed: {request.method} {request.url} - "
            f"Status: {response.status_code}"
        )
        return response
    
    # Log errors
    @app.errorhandler(Exception)
    def log_exception(error):
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        # Re-raise the error so Flask handles it normally
        raise error


class PerformanceLogger:
    """Context manager for logging performance metrics."""
    
    def __init__(self, operation_name: str, logger: logging.Logger = None):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"Operation completed: {self.operation_name} "
                f"in {duration:.2f} seconds"
            )
        else:
            self.logger.error(
                f"Operation failed: {self.operation_name} "
                f"after {duration:.2f} seconds - {exc_val}"
            )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


def initialize_application_logging():
    """Initialize logging for the entire application."""
    
    # Get configuration from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/farmacia.log')
    
    # Set up basic logging
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        enable_console=True
    )
    
    # Set up error handling
    setup_error_handling()
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("CEAF Farmácia application logging initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_file}")


if __name__ == "__main__":
    # Test logging setup
    initialize_application_logging()
    
    logger = logging.getLogger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test performance logger
    with PerformanceLogger("test_operation", logger):
        import time
        time.sleep(1)
    
    print("Logging test completed. Check logs directory.")