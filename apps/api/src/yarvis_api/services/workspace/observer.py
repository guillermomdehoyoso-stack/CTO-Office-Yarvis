from __future__ import annotations

from datetime import UTC, datetime

from yarvis_api.services.workspace.models import WorkspaceState


class EngineeringObserver:
    def observe(
        self,
        repository_health: dict[str, object],
        state: WorkspaceState,
        timeline: list[dict[str, str | int]],
    ) -> dict[str, object]:
        observations: list[str] = []
        recommendations: list[str] = []
        blockers: list[str] = []

        total_files = int(repository_health.get("total_files", 0))
        if total_files == 0:
            blockers.append("Repository scanner found zero files; verify repository root configuration.")
        else:
            observations.append(f"Repository scanner indexed {total_files} files.")

        observations.append(f"Current sprint: {state.current_sprint}")
        observations.append(f"Current gate: {state.current_gate}")

        if "EOS Foundation Documentation" in state.current_gate:
            recommendations.append("Keep WS-000 implementation outside docs/eos gate scope.")

        docs_count = int(repository_health.get("documentation_files", 0))
        code_count = int(repository_health.get("python_files", 0)) + int(repository_health.get("typescript_files", 0))
        if docs_count > code_count:
            recommendations.append("Prioritize compiling software increments over additional documentation-only changes.")

        if timeline:
            latest_path = str(timeline[0].get("path", "UNKNOWN"))
            observations.append(f"Most recent repository change: {latest_path}")

        health = "healthy"
        if blockers:
            health = "blocked"
        elif state.current_sprint == "UNKNOWN" or state.current_gate == "UNKNOWN":
            health = "degraded"

        return {
            "observations": observations,
            "recommendations": recommendations,
            "blockers": blockers,
            "next_action": "Implement WS-000 platform modules and validate API/UI acceptance criteria.",
            "engineering_health": health,
            "generated_at": datetime.now(tz=UTC).isoformat(),
        }
