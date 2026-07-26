"""WS-001 application-layer contracts and boundaries.

This package defines transport-neutral application contracts used by
incremental WS-001 implementation work.
"""

from yarvis_api.application.contracts import (
    WS001CommandName,
    WS001EventName,
    WS001QueryName,
    WS002CommandName,
    WS002QueryName,
    command_contracts,
    event_contracts,
    query_contracts,
)
from yarvis_api.application.authentication import (
    AuthenticatedPrincipal,
    TransportAuthenticationRequest,
)
from yarvis_api.application.errors import (
    ApplicationError,
    ApplicationErrorCode,
)
from yarvis_api.application.inbound_intake import (
    InboundInboxPort,
    InboundIntakeResult,
    InboundIntakeSubmission,
    InboundMessageFixture,
    InboundSourceType,
)
from yarvis_api.application.metadata import (
    ActorContext,
    ActorType,
    AuthorityContext,
    RequestMetadata,
)
from yarvis_api.application.operational_context import AssociateIntakeOperationalContextCommand
from yarvis_api.application.mission_inbox import MissionInboxFilters

__all__ = [
    "AuthenticatedPrincipal",
    "ActorContext",
    "ActorType",
    "ApplicationError",
    "ApplicationErrorCode",
    "AuthorityContext",
    "InboundInboxPort",
    "InboundIntakeResult",
    "InboundIntakeSubmission",
    "InboundMessageFixture",
    "InboundSourceType",
    "RequestMetadata",
    "TransportAuthenticationRequest",
    "WS001CommandName",
    "WS001EventName",
    "WS001QueryName",
    "WS002CommandName",
    "WS002QueryName",
    "AssociateIntakeOperationalContextCommand",
    "MissionInboxFilters",
    "command_contracts",
    "event_contracts",
    "query_contracts",
]
