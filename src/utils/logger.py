"""
Logger Utility - Configurable logging with colored output and file rotation
"""

import logging
import logging.handlers
import os
import colorlog
from typing import Dict, Any


def setup_logger(config: Dict[str, Any], log_level: str = None) -> logging.Logger:
    """Setup and configure logger"""
    
    # Create logs directory if it doesn't exist
    log_file = config.get('file', './logs/edge_sdk.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Get log level
    level = log_level or config.get('level', 'INFO')
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    
    # Color formatter for console
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.get('file'):
        max_bytes = config.get('max_size_mb', 10) * 1024 * 1024  # Convert MB to bytes
        backup_count = config.get('backup_count', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            config['file'],
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        
        # File formatter (no colors)
        file_formatter = logging.Formatter(
            config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(self.__class__.__name__)