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

@dataclass(frozen=True, slots=True)
class AssignOpportunityTemplateCommand:
    workspace_id: UUID
    opportunity_type: str
    expected_version: int


@dataclass(frozen=True, slots=True)
class PublishDossierTemplateVersionCommand:
    stable_key: str
    business_type: str
    business_version: int
    display_name: str


@dataclass(frozen=True, slots=True)
class RetireDossierTemplateVersionCommand:
    template_id: UUID
    expected_version: int
