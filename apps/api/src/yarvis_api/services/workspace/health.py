from __future__ import annotations

from typing import Protocol


class HealthProvider(Protocol):
    def evaluate(self, snapshot: dict[str, object]) -> tuple[str, str]:
        ...


class StaticWorkspaceServiceHealthProvider:
    def evaluate(self, snapshot: dict[str, object]) -> tuple[str, str]:
        return ("workspace_api", "ok")


class RepositoryScannerHealthProvider:
    def evaluate(self, snapshot: dict[str, object]) -> tuple[str, str]:
        status = "ok" if int(snapshot["repository"].get("total_files", 0)) > 0 else "degraded"
        return ("repository_scanner", status)


class ObserverHealthProvider:
    def evaluate(self, snapshot: dict[str, object]) -> tuple[str, str]:
        value = str(snapshot["observer"].get("engineering_health", "unknown"))
        return ("engineering_observer", "ok" if value in {"healthy", "degraded"} else "degraded")


class HealthService:
    def __init__(self, providers: list[HealthProvider] | None = None):
        self._providers = providers or [
            StaticWorkspaceServiceHealthProvider(),
            RepositoryScannerHealthProvider(),
            ObserverHealthProvider(),
        ]

    def evaluate(self, snapshot: dict[str, object]) -> dict[str, str]:
        services: dict[str, str] = {}
        for provider in self._providers:
            key, value = provider.evaluate(snapshot)
            services[key] = value
        return services
