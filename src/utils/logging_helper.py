"""
Logging utilities for the scraper.

Provides structured logging setup with consistent formatting and
context management.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def setup_logging(config: Dict[str, Any], log_level: str = "INFO") -> None:
    """Setup logging configuration for the scraper.
    
    Args:
        config: Configuration dictionary
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"scraper_{timestamp}.log"
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Setup root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('assemblyai').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with consistent configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class ContextLogger:
    """Logger wrapper that adds context to log messages."""
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        """Initialize context logger.
        
        Args:
            logger: Base logger instance
            context: Context information to add to messages
        """
        self.logger = logger
        self.context = context
    
    def _format_message(self, message: str) -> str:
        """Format message with context information.
        
        Args:
            message: Original log message
            
        Returns:
            Formatted message with context
        """
        if self.context:
            context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"[{context_str}] {message}"
        return message
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with context."""
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with context."""
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with context."""
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with context."""
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message with context."""
        self.logger.critical(self._format_message(message), *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception message with context."""
        self.logger.exception(self._format_message(message), *args, **kwargs)


def get_context_logger(name: str, context: Dict[str, Any]) -> ContextLogger:
    """Get a context logger with additional information.
    
    Args:
        name: Logger name
        context: Context information to include in messages
        
    Returns:
        Context logger instance
    """
    base_logger = get_logger(name)
    return ContextLogger(base_logger, context)


class LoggingMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
        self._context = {}
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if self._logger is None:
            self._logger = get_logger(self.__class__.__module__ + '.' + self.__class__.__name__)
        return self._logger
    
    def set_logging_context(self, context: Dict[str, Any]) -> None:
        """Set logging context for this instance.
        
        Args:
            context: Context information to add to log messages
        """
        self._context.update(context)
    
    def get_context_logger(self) -> ContextLogger:
        """Get context logger for this instance.
        
        Returns:
            Context logger with instance context
        """
        return ContextLogger(self.logger, self._context)
    
    def log_debug(self, message: str, **extra_context):
        """Log debug message with context."""
        context = {**self._context, **extra_context}
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            message = f"[{context_str}] {message}"
        self.logger.debug(message)
    
    def log_info(self, message: str, **extra_context):
        """Log info message with context."""
        context = {**self._context, **extra_context}
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            message = f"[{context_str}] {message}"
        self.logger.info(message)
    
    def log_warning(self, message: str, **extra_context):
        """Log warning message with context."""
        context = {**self._context, **extra_context}
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            message = f"[{context_str}] {message}"
        self.logger.warning(message)
    
    def log_error(self, message: str, **extra_context):
        """Log error message with context."""
        context = {**self._context, **extra_context}
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            message = f"[{context_str}] {message}"
        self.logger.error(message)


def log_function_call(func):
    """Decorator to log function calls with arguments and results."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Log function entry
        logger.debug(f"Calling {func_name}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func_name}")
            return result
        except Exception as e:
            logger.error(f"Error in {func_name}: {e}")
            raise
    
    return wrapper


def log_performance(func):
    """Decorator to log function performance metrics."""
    def wrapper(*args, **kwargs):
        import time
        
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func_name} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func_name} failed after {duration:.2f}s: {e}")
            raise
    
    return wrapper
