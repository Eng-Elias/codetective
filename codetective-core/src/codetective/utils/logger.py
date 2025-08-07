"""
Logging utilities for the codetective system.
"""

import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Any
from loguru import logger as loguru_logger


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Logger:
    """
    Centralized logging management for the codetective system.
    
    This class provides a unified interface for logging across all components,
    with support for different log levels, file output, and structured logging.
    """
    
    def __init__(self, log_level: LogLevel = LogLevel.INFO, log_file: Optional[Path] = None):
        """
        Initialize the logger.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional path to log file
        """
        self.log_level = log_level
        self.log_file = log_file
        self._configured = False
        
        # Configure logger on first use
        self._configure_logger()
    
    def _configure_logger(self) -> None:
        """Configure the loguru logger with appropriate settings."""
        if self._configured:
            return
        
        # Remove default handler
        loguru_logger.remove()
        
        # Add console handler with formatting
        loguru_logger.add(
            sys.stderr,
            level=self.log_level.value,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
        )
        
        # Add file handler if specified
        if self.log_file:
            loguru_logger.add(
                str(self.log_file),
                level=self.log_level.value,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                rotation="10 MB",
                retention="7 days",
                compression="zip",
            )
        
        self._configured = True
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        loguru_logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        loguru_logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        loguru_logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        loguru_logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        loguru_logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        loguru_logger.exception(message, **kwargs)
    
    def bind(self, **kwargs: Any) -> "Logger":
        """Bind additional context to logger."""
        bound_logger = loguru_logger.bind(**kwargs)
        
        # Create new Logger instance with bound logger
        new_logger = Logger.__new__(Logger)
        new_logger.log_level = self.log_level
        new_logger.log_file = self.log_file
        new_logger._configured = True
        new_logger._logger = bound_logger
        
        return new_logger
    
    def set_level(self, level: LogLevel) -> None:
        """Change the logging level."""
        self.log_level = level
        # Reconfigure logger with new level
        self._configured = False
        self._configure_logger()
    
    def add_file_handler(self, file_path: Path, level: Optional[str] = None) -> None:
        """Add additional file handler."""
        loguru_logger.add(
            str(file_path),
            level=level or self.log_level.value,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )
    
    @classmethod
    def get_logger(cls, name: str, **kwargs: Any) -> "Logger":
        """Get a logger instance with specific name and context."""
        logger_instance = cls(**kwargs)
        return logger_instance.bind(name=name)


# Global logger instance
_global_logger = Logger()

# Convenience functions for global logger
def debug(message: str, **kwargs: Any) -> None:
    """Log debug message using global logger."""
    _global_logger.debug(message, **kwargs)

def info(message: str, **kwargs: Any) -> None:
    """Log info message using global logger."""
    _global_logger.info(message, **kwargs)

def warning(message: str, **kwargs: Any) -> None:
    """Log warning message using global logger."""
    _global_logger.warning(message, **kwargs)

def error(message: str, **kwargs: Any) -> None:
    """Log error message using global logger."""
    _global_logger.error(message, **kwargs)

def critical(message: str, **kwargs: Any) -> None:
    """Log critical message using global logger."""
    _global_logger.critical(message, **kwargs)

def exception(message: str, **kwargs: Any) -> None:
    """Log exception using global logger."""
    _global_logger.exception(message, **kwargs)

def configure_global_logger(log_level: LogLevel = LogLevel.INFO, log_file: Optional[Path] = None) -> None:
    """Configure the global logger."""
    global _global_logger
    _global_logger = Logger(log_level, log_file)
