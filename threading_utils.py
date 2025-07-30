#!/usr/bin/env python3
"""
Threading Utilities for Jetson Orin Integration SDK

This file contains utilities for safe concurrent operations and
threading management.

Author: Jetson Orin SDK
"""

import threading
import time
from typing import Any, Callable, Optional
from functools import wraps

class ThreadSafeResource:
    """Base class for thread-safe resources."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._cleanup_lock = threading.Lock()
        self._is_cleaned_up = False
    
    def _acquire_lock(self, timeout: float = 5.0) -> bool:
        """Acquire the resource lock with timeout."""
        return self._lock.acquire(timeout=timeout)
    
    def _release_lock(self):
        """Release the resource lock."""
        if self._lock.locked():
            self._lock.release()
    
    def cleanup(self):
        """Clean up the resource in a thread-safe manner."""
        with self._cleanup_lock:
            if not self._is_cleaned_up:
                self._perform_cleanup()
                self._is_cleaned_up = True
    
    def _perform_cleanup(self):
        """Override this method to implement specific cleanup logic."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        if not self._acquire_lock():
            raise RuntimeError("Could not acquire resource lock")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._release_lock()

def thread_safe_operation(timeout: float = 5.0):
    """
    Decorator for thread-safe operations.
    
    Args:
        timeout: Lock acquisition timeout in seconds
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, '_lock'):
                if self._lock.acquire(timeout=timeout):
                    try:
                        return func(self, *args, **kwargs)
                    finally:
                        self._lock.release()
                else:
                    raise RuntimeError(f"Could not acquire lock for {func.__name__}")
            else:
                return func(self, *args, **kwargs)
        return wrapper
    return decorator

def safe_thread_creation(target: Callable, *args, **kwargs) -> threading.Thread:
    """
    Safely create and start a thread.
    
    Args:
        target: Function to run in thread
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Started thread
    """
    thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True  # Ensure thread doesn't prevent program exit
    thread.start()
    return thread

def wait_for_threads(threads: list, timeout: float = 10.0) -> bool:
    """
    Wait for multiple threads to complete.
    
    Args:
        threads: List of threads to wait for
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if all threads completed, False if timeout occurred
    """
    start_time = time.time()
    for thread in threads:
        remaining_time = timeout - (time.time() - start_time)
        if remaining_time <= 0:
            return False
        thread.join(timeout=remaining_time)
        if thread.is_alive():
            return False
    return True

class ResourceManager:
    """Manages thread-safe resource cleanup."""
    
    def __init__(self):
        self._resources = []
        self._lock = threading.Lock()
    
    def register_resource(self, resource: ThreadSafeResource):
        """Register a resource for cleanup."""
        with self._lock:
            self._resources.append(resource)
    
    def cleanup_all(self):
        """Clean up all registered resources."""
        with self._lock:
            for resource in self._resources:
                try:
                    resource.cleanup()
                except Exception as e:
                    print(f"Error cleaning up resource: {e}")
            self._resources.clear()
    
    def __del__(self):
        """Ensure cleanup on destruction."""
        self.cleanup_all()

# Global resource manager
_global_resource_manager = ResourceManager()

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager."""
    return _global_resource_manager

def register_global_resource(resource: ThreadSafeResource):
    """Register a resource with the global manager."""
    _global_resource_manager.register_resource(resource)

def cleanup_global_resources():
    """Clean up all globally registered resources."""
    _global_resource_manager.cleanup_all()
