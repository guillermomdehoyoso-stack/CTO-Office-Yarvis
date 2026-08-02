"""DI-003 Slice 01 application commands."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProposeOpportunityCommand:
    business_intent: str


@dataclass(frozen=True, slots=True)
class ConfirmOpportunityCommand:
    opportunity_id: UUID
    expected_version: int
