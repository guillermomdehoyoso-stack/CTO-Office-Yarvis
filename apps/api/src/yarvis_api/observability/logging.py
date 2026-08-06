"""Structured application logging that redacts untrusted diagnostic values."""

from __future__ import annotations

import json
import logging
from typing import Any

from yarvis_api.observability.redaction import sanitize_mapping


class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        fields: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "observability", None)
        if isinstance(extra, dict):
            fields.update(sanitize_mapping(extra))
        return json.dumps(sanitize_mapping(fields), sort_keys=True, default=str)


def configure_structured_logging(level: str) -> logging.Logger:
    logger = logging.getLogger("yarvis.observability")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredLogFormatter())
        logger.addHandler(handler)
    return logger


def emit_observability_event(logger: logging.Logger, event: str, **fields: object) -> None:
    logger.info(event, extra={"observability": {"event": event, **fields}})
