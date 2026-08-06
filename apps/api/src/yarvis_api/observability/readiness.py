"""Liveness and dependency readiness checks without worker/scheduler scope."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text

from yarvis_api.persistence import PersistenceRuntime


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    ready: bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReadinessProbe:
    persistence: PersistenceRuntime

    def check(self, *, lifecycle_active: bool, registries_sealed: bool) -> ReadinessReport:
        if not lifecycle_active:
            return ReadinessReport(False, "application lifecycle is inactive")
        if not registries_sealed:
            return ReadinessReport(False, "required registries are not sealed")
        if self.persistence.is_disposed:
            return ReadinessReport(False, "persistence runtime is disposed")
        try:
            with self.persistence.create_session() as session:
                session.execute(text("SELECT 1"))
        except Exception:
            return ReadinessReport(False, "technical dependency is unavailable")
        return ReadinessReport(True)
