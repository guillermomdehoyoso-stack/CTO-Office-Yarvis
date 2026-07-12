from datetime import datetime, timezone


def utc_now() -> datetime:
    """Central UTC clock; tests patch this function for deterministic time."""
    return datetime.now(timezone.utc)
