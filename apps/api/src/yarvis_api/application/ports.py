"""Vendor-neutral application ports for WS-001 bounded contexts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from yarvis_api.application.authentication import AuthenticatedPrincipal, TransportAuthenticationRequest


@dataclass(frozen=True, slots=True)
class AuthorityEvaluation:
    allowed: bool
    rationale: str


class GovernancePort(Protocol):
    def evaluate_authority(self, *, actor_id: str, authority_scope: str) -> AuthorityEvaluation: ...


class AuthenticationPort(Protocol):
    def authenticate(self, request: TransportAuthenticationRequest) -> AuthenticatedPrincipal: ...


class IdentityPort(Protocol):
    def resolve_subject_candidate(self, *, raw_subject: str) -> str: ...


class ObservationEvidencePort(Protocol):
    def capture_inbound_observation(self, *, source_ref: str, payload: dict[str, str]) -> str: ...


class ExecutionPort(Protocol):
    def create_pending_action(self, *, case_id: str, reason: str) -> str: ...


class MissionControlPort(Protocol):
    def publish_attention(self, *, case_id: str, summary: str) -> str: ...


class NetpayOperationsPort(Protocol):
    def open_case(self, *, merchant_candidate_id: str, channel: str) -> str: ...
