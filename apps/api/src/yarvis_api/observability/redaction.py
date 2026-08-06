"""Small, deterministic redaction boundary for F-012 public diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

_SENSITIVE_TOKENS = frozenset({"authorization", "cookie", "credential", "password", "secret", "token", "api_key"})
_SENSITIVE_TEXT_MARKERS = frozenset({"bearer ", "password=", "secret=", "token=", "api_key="})
_INTERNAL_TEXT_TOKENS = frozenset(
    {"sqlalchemy", "traceback", "postgres", "psycopg", "database error", "select ", "insert ", "update ", "delete "}
)
_REDACTED = "[REDACTED]"
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:password|passwd|pwd|token|access_token|refresh_token|id_token|authorization|api[_-]?key|apikey|secret|client_secret|cookie|set-cookie)\b(?:['\"])?\s*[:=]\s*(?:['\"])?)(?:(?:bearer|basic)\s+)?"
    r"(?!\[REDACTED\])[^\s,;'\"}\]]+(?:['\"])?"
)


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return any(token in normalized for token in _SENSITIVE_TOKENS)


def sanitize_text(value: object) -> str:
    """Return a bounded diagnostic string without common secret-bearing values."""

    text = str(value)
    lowered = text.lower()
    if any(token in lowered for token in _INTERNAL_TEXT_TOKENS):
        return _REDACTED
    return _SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}{_REDACTED}", text)[:512]


def sanitize_value(value: Any, *, key: object | None = None) -> Any:
    if key is not None and _is_sensitive_key(key):
        return _REDACTED
    if isinstance(value, Mapping):
        return {str(item_key): sanitize_value(item_value, key=item_key) for item_key, item_value in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [sanitize_value(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return sanitize_text(value)


def sanitize_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): sanitize_value(item, key=key) for key, item in value.items()}
