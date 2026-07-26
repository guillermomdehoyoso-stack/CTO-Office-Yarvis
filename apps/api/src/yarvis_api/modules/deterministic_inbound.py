from __future__ import annotations

from dataclasses import dataclass

from yarvis_api.application.inbound_intake import InboundMessageFixture
from yarvis_api.schemas.intake import DeterministicInboundIntakeCreate


@dataclass(frozen=True, slots=True)
class DeterministicInboundInboxAdapter:
    """Offline adapter that maps the API submission into the canonical inbound fixture."""

    def adapt(self, submission: DeterministicInboundIntakeCreate) -> InboundMessageFixture:
        return InboundMessageFixture(
            external_source=submission.external_source,
            external_message_id=submission.external_message_id,
            connector_delivery_id=submission.connector_delivery_id,
            sender=submission.sender,
            recipients=tuple(submission.recipients),
            subject=submission.subject,
            text_body=submission.text_body,
            source_timestamp=submission.source_timestamp,
            received_timestamp=submission.received_timestamp,
            content_type=submission.content_type,
            html_body=submission.html_body,
            headers=dict(submission.headers),
        )
