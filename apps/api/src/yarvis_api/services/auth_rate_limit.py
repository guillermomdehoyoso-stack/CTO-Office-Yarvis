"""Sanitized authentication rate-limit abstraction and local/test backend."""

from __future__ import annotations

import hashlib
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode


class AuthRateLimitBackend(Protocol):
    def consume(self, namespace: str, key_hash: str, limit: int, window_seconds: int) -> bool: ...


class InMemoryAuthRateLimitBackend:
    """Process-local backend allowed only for local/test or one-replica deployments."""

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def consume(self, namespace: str, key_hash: str, limit: int, window_seconds: int) -> bool:
        now = monotonic()
        with self._lock:
            entries = self._entries[(namespace, key_hash)]
            while entries and entries[0] <= now - window_seconds:
                entries.popleft()
            if len(entries) >= limit:
                return False
            entries.append(now)
            return True


@dataclass(slots=True)
class AuthRateLimiter:
    backend: AuthRateLimitBackend

    def require(self, namespace: str, raw_key: str, *, limit: int, window_seconds: int) -> None:
        key_hash = hashlib.sha256(f"yarvis-auth:{namespace}:{raw_key}".encode()).hexdigest()
        if not self.backend.consume(namespace, key_hash, limit, window_seconds):
            raise ApplicationError(
                ApplicationErrorCode.AUTHORIZATION_DENIED,
                "request denied",
                {"reason": "rate_limited"},
            )
