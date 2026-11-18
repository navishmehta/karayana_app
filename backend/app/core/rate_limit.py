"""Simple in-memory rate limiter (sliding window).

Good for one API process. If the API is later run with several workers/servers,
swap the storage for Redis behind the same `hit()` method.
"""

import threading
import time
from collections import defaultdict, deque
from enum import StrEnum

from app.core.config import get_settings
from app.core.constants import RATE_LIMIT_WINDOW_SECONDS
from app.core.errors import AppError
from app.enums.error_code import ErrorCode


class RateLimitRule(StrEnum):
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"

    @property
    def per_minute(self) -> int:
        settings = get_settings()
        return {
            RateLimitRule.LOGIN: settings.rate_limit_login_per_minute,
            RateLimitRule.PASSWORD_RESET: settings.rate_limit_password_reset_per_minute,
        }[self]


class RateLimiter:
    def __init__(self, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS) -> None:
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, rule: RateLimitRule, key: str) -> None:
        """Count one attempt; raise TOO_MANY_REQUESTS (with Retry-After) when over the limit."""
        now = time.monotonic()
        bucket_key = f"{rule}:{key.lower()}"
        with self._lock:
            hits = self._hits[bucket_key]
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= rule.per_minute:
                retry_after = int(self._window - (now - hits[0])) + 1
                raise AppError(ErrorCode.TOO_MANY_REQUESTS, headers={"Retry-After": str(retry_after)})
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


rate_limiter = RateLimiter()
