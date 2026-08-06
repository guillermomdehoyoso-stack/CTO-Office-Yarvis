"""PostgreSQL adapter for F-012 append-only technical trace records."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from yarvis_api.models.application_trace import ApplicationTrace
from yarvis_api.persistence.runtime import PersistenceRuntime


class ApplicationTraceStore:
    """Uses an explicit technical session, never a Command Unit of Work."""

    def __init__(self, persistence: PersistenceRuntime) -> None:
        self._persistence = persistence

    def append(self, entry: ApplicationTrace) -> None:
        with self._persistence.create_session() as session:
            session.add(entry)
            session.commit()

    def list_by_trace_id(self, trace_id: UUID) -> tuple[ApplicationTrace, ...]:
        with self._persistence.create_session() as session:
            return tuple(
                session.scalars(
                    select(ApplicationTrace)
                    .where(ApplicationTrace.trace_id == trace_id)
                    .order_by(ApplicationTrace.sequence.asc())
                )
            )

    def list_by_correlation_id(self, correlation_id: str) -> tuple[ApplicationTrace, ...]:
        with self._persistence.create_session() as session:
            return tuple(
                session.scalars(
                    select(ApplicationTrace)
                    .where(ApplicationTrace.correlation_id == correlation_id)
                    .order_by(ApplicationTrace.trace_id.asc(), ApplicationTrace.sequence.asc())
                )
            )

    def count(self) -> int:
        with self._persistence.create_session() as session:
            return len(tuple(session.scalars(select(ApplicationTrace.id))))
