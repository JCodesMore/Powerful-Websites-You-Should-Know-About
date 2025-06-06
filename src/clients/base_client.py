"""
Base API client with common functionality for all external service clients.

Provides retry logic, rate limiting, error handling, and logging.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, TypeVar
from functools import wraps

from ..exceptions import APIError, RateLimitError, RetryableError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseAPIClient(ABC):
    """Base class for all API clients."""
    
    def __init__(self, api_name: str, config: Dict[str, Any]):
        """Initialize base API client.
        
        Args:
            api_name: Name of the API service
            config: Configuration dictionary
        """
        self.api_name = api_name
        self.config = config
        self.max_retries = config.get('rate_limits', {}).get('max_retries', 3)
        self.retry_delay = config.get('rate_limits', {}).get('retry_delay', 5)
        self.rate_limit_rpm = config.get('rate_limits', {}).get(f'{api_name.lower()}_rpm', 60)
        
        # Track API calls for rate limiting
        self._last_call_time = 0
        self._call_count = 0
        self._call_window_start = time.time()
    
    def _check_rate_limit(self) -> None:
        """Check if we're within rate limits."""
        current_time = time.time()
        
        # Reset counter if we're in a new minute window
        if current_time - self._call_window_start >= 60:
            self._call_count = 0
            self._call_window_start = current_time
        
        # Check if we've exceeded the rate limit
        if self._call_count >= self.rate_limit_rpm:
            wait_time = 60 - (current_time - self._call_window_start)
            if wait_time > 0:
                logger.warning(f"Rate limit reached for {self.api_name}, waiting {wait_time:.1f}s")
                raise RateLimitError(self.api_name, int(wait_time))
        
        self._call_count += 1
        self._last_call_time = current_time
    
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if an error should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if the error should be retried
        """
        if attempt >= self.max_retries:
            return False
        
        # Always retry rate limit errors
        if isinstance(error, RateLimitError):
            return True
        
        # Retry other retryable errors
        if isinstance(error, RetryableError):
            return True
        
        # Retry specific API errors (connection issues, timeouts, etc.)
        if isinstance(error, APIError):
            # Retry on server errors (5xx) but not client errors (4xx)
            if hasattr(error, 'status_code') and error.status_code:
                return 500 <= error.status_code < 600
        
        return False
    
    def _calculate_retry_delay(self, attempt: int, error: Exception) -> float:
        """Calculate delay before retry.
        
        Args:
            attempt: Current attempt number (0-based)
            error: The exception that occurred
            
        Returns:
            Delay in seconds
        """
        if isinstance(error, RateLimitError) and error.retry_after:
            return error.retry_after
        
        # Exponential backoff with jitter
        base_delay = self.retry_delay * (2 ** attempt)
        jitter = base_delay * 0.1  # 10% jitter
        return base_delay + jitter
    
    def with_retry(self, func: Callable[[], T]) -> T:
        """Execute a function with retry logic.
        
        Args:
            func: Function to execute
            
        Returns:
            Function result
            
        Raises:
            APIError: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self._check_rate_limit()
                return func()
            
            except Exception as e:
                last_error = e
                
                if not self._should_retry(e, attempt):
                    logger.error(f"{self.api_name} API call failed permanently: {e}")
                    raise
                
                delay = self._calculate_retry_delay(attempt, e)
                logger.warning(f"{self.api_name} API call failed (attempt {attempt + 1}), "
                             f"retrying in {delay:.1f}s: {e}")
                time.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_error or APIError(f"All retry attempts failed for {self.api_name}", self.api_name)
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the client is properly configured.
        
        Returns:
            True if the client has valid configuration
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test the API connection.
        
        Returns:
            True if connection is successful
        """
        pass


def api_call(func: Callable) -> Callable:
    """Decorator to wrap API calls with retry logic and error handling."""
    
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not isinstance(self, BaseAPIClient):
            raise TypeError("api_call decorator can only be used on BaseAPIClient methods")
        
        def api_func():
            return func(self, *args, **kwargs)
        
        return self.with_retry(api_func)
    
    return wrapper
