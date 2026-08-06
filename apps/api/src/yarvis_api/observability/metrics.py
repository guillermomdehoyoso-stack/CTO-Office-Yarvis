"""Dependency-free, per-application technical metrics for F-012."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass(slots=True)
class ObservabilityMetrics:
    """Bounded metrics with no tenant, actor, object, or payload labels."""

    _counters: dict[str, int] = field(default_factory=dict)
    _durations: dict[str, dict[str, float | int]] = field(default_factory=dict)
    _gauges: dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def observe_duration(self, name: str, seconds: float) -> None:
        with self._lock:
            value = max(seconds, 0.0)
            aggregate = self._durations.setdefault(name, {"count": 0, "sum_seconds": 0.0, "min_seconds": value, "max_seconds": value})
            aggregate["count"] = int(aggregate["count"]) + 1
            aggregate["sum_seconds"] = float(aggregate["sum_seconds"]) + value
            aggregate["min_seconds"] = min(float(aggregate["min_seconds"]), value)
            aggregate["max_seconds"] = max(float(aggregate["max_seconds"]), value)

    def set_gauge(self, name: str, value: int) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "counters": dict(sorted(self._counters.items())),
                "gauges": dict(sorted(self._gauges.items())),
                "durations": {
                    name: dict(values) for name, values in sorted(self._durations.items())
                },
            }
