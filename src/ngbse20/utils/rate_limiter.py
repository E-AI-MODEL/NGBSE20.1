"""
Rate limiting utilities for NGBSE 20.2.
Provides rate limiting and retry logic for API calls.
"""

import time
import random
from typing import Dict, Callable, Any
from functools import wraps
from ..logging import get_logger

LOGGER = get_logger(__name__)


class RateLimiter:
    """Simple rate limiter with exponential backoff."""

    def __init__(self, max_requests: int = 60, time_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limit."""
        now = time.time()
        # Remove requests outside the time window
        self.requests = [
            req_time for req_time in self.requests if now - req_time < self.time_window
        ]

        return len(self.requests) < self.max_requests

    def record_request(self):
        """Record a request timestamp."""
        self.requests.append(time.time())

    def wait_time(self) -> float:
        """Calculate how long to wait before next request."""
        if self.can_make_request():
            return 0.0

        # Calculate time until oldest request expires
        now = time.time()
        oldest_request = min(self.requests)
        return (oldest_request + self.time_window) - now


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_retries:
                        LOGGER.error(
                            f"Function {func.__name__} failed after {max_retries} "
                            f"retries: {e}"
                        )
                        raise e

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay *= 0.5 + random.random() * 0.5

                    LOGGER.warning(
                        f"Function {func.__name__} failed (attempt "
                        f"{attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator


def rate_limited(rate_limiter: RateLimiter):
    """
    Decorator for rate limiting function calls.

    Args:
        rate_limiter: RateLimiter instance to use
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Wait if necessary
            wait_time = rate_limiter.wait_time()
            if wait_time > 0:
                LOGGER.debug(
                    f"Rate limiting: waiting {wait_time:.2f}s before {func.__name__}"
                )
                time.sleep(wait_time)

            # Record the request
            rate_limiter.record_request()

            # Execute the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


class APIRateLimiter:
    """Rate limiter specifically for API calls with different limits per service."""

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {
            "shodan": RateLimiter(
                max_requests=1, time_window=1
            ),  # 1 request per second
            "censys": RateLimiter(
                max_requests=5, time_window=1
            ),  # 5 requests per second
            "leakix": RateLimiter(
                max_requests=10, time_window=1
            ),  # 10 requests per second
            "urlscan": RateLimiter(
                max_requests=1, time_window=1
            ),  # 1 request per second
            "github": RateLimiter(
                max_requests=10, time_window=1
            ),  # 10 requests per second
            "news": RateLimiter(
                max_requests=100, time_window=1
            ),  # 100 requests per second
            "default": RateLimiter(
                max_requests=10, time_window=1
            ),  # Default: 10 requests per second
        }

    def get_limiter(self, service: str) -> RateLimiter:
        """Get rate limiter for a specific service."""
        return self.limiters.get(service.lower(), self.limiters["default"])

    def wait_for_service(self, service: str):
        """Wait for rate limit on a specific service."""
        limiter = self.get_limiter(service)
        wait_time = limiter.wait_time()
        if wait_time > 0:
            LOGGER.debug(f"Rate limiting {service}: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        limiter.record_request()


# Global rate limiter instance
api_rate_limiter = APIRateLimiter()


def api_rate_limited(service: str):
    """
    Decorator for API rate limiting.

    Args:
        service: API service name (shodan, censys, etc.)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            api_rate_limiter.wait_for_service(service)
            return func(*args, **kwargs)

        return wrapper

    return decorator
