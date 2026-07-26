"""Transport-neutral WS-002A command and read contracts."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AssociateIntakeOperationalContextCommand:
    intake_item_id: UUID
    site_id: UUID
    project_id: UUID
    connector_mapping_id: UUID | None = None
