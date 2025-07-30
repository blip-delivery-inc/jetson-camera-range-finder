#!/usr/bin/env python3
"""
Error Handling Utilities for Jetson Orin Integration SDK

This file contains utility functions for consistent error handling
across the SDK.

Author: Jetson Orin SDK
"""

import logging
from typing import Optional, Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)

def safe_operation(operation_name: str, default_return: Any = None):
    """
    Decorator for safe operations with error handling.
    
    Args:
        operation_name: Name of the operation for logging
        default_return: Default value to return on error
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                return default_return
        return wrapper
    return decorator

def validate_not_none(value: Any, name: str) -> bool:
    """
    Validate that a value is not None.
    
    Args:
        value: Value to check
        name: Name of the value for error messages
    
    Returns:
        True if value is not None, False otherwise
    """
    if value is None:
        logger.warning(f"{name} is None")
        return False
    return True

def validate_positive(value: float, name: str) -> bool:
    """
    Validate that a value is positive.
    
    Args:
        value: Value to check
        name: Name of the value for error messages
    
    Returns:
        True if value is positive, False otherwise
    """
    if value <= 0:
        logger.warning(f"{name} must be positive, got {value}")
        return False
    return True

def safe_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Perform safe division with zero check.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if division by zero
    
    Returns:
        Result of division or default value
    """
    if denominator == 0:
        logger.warning("Division by zero attempted")
        return default
    return numerator / denominator

def safe_file_operation(file_path: str, operation: str, default_return: Any = None):
    """
    Perform safe file operations with error handling.
    
    Args:
        file_path: Path to the file
        operation: Operation to perform ('read', 'write', 'delete')
        default_return: Default value to return on error
    
    Returns:
        Result of operation or default value
    """
    try:
        if operation == 'read':
            with open(file_path, 'r') as f:
                return f.read()
        elif operation == 'write':
            with open(file_path, 'w') as f:
                return f.write()
        elif operation == 'delete':
            import os
            os.remove(file_path)
            return True
        else:
            logger.error(f"Unknown file operation: {operation}")
            return default_return
    except Exception as e:
        logger.error(f"File operation '{operation}' failed for {file_path}: {e}")
        return default_return

def validate_device_path(path: str) -> bool:
    """
    Validate device path format.
    
    Args:
        path: Device path to validate
    
    Returns:
        True if path is valid, False otherwise
    """
    import re
    
    # Check for common device path patterns
    patterns = [
        r'^/dev/video\d+$',  # Video devices
        r'^/dev/tty[A-Z]+\d*$',  # Serial devices
        r'^/dev/usb\d+$',  # USB devices
    ]
    
    for pattern in patterns:
        if re.match(pattern, path):
            return True
    
    logger.warning(f"Invalid device path format: {path}")
    return False

def validate_port_number(port: int) -> bool:
    """
    Validate port number range.
    
    Args:
        port: Port number to validate
    
    Returns:
        True if port is valid, False otherwise
    """
    if not isinstance(port, int) or port < 1 or port > 65535:
        logger.warning(f"Invalid port number: {port}")
        return False
    return True

def validate_baudrate(baudrate: int) -> bool:
    """
    Validate baudrate value.
    
    Args:
        baudrate: Baudrate to validate
    
    Returns:
        True if baudrate is valid, False otherwise
    """
    valid_baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
    if baudrate not in valid_baudrates:
        logger.warning(f"Invalid baudrate: {baudrate}")
        return False
    return True
