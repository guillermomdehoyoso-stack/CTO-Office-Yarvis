# Yarvis Domain Boundaries

## Purpose

Define the current architectural boundaries for Yarvis so the domain can evolve without collapsing into a single undifferentiated model. These boundaries separate operational meaning from transport, infrastructure, and intelligence.

## Boundary 1: Interaction / Intake

This boundary covers how information enters Yarvis from users or channels.

Includes:
- manual text entry;
- uploaded files;
- attachments registered as metadata;
- conversational intake;
- classification suggestions;
- context confirmation.

Permitted dependencies:
- Operational Core for case and checklist updates;
- Evidence and Documents for durable storage of received material;
- Identity and Relationships for validating involved actors;
- Intelligence for classification or summarization proposals;
- Trust and Security for permissions, confirmation, and audit requirements;
- Infrastructure and Integrations for transport and storage adapters.

Prohibited dependencies:
- direct dependence on a specific AI provider;
- direct dependence on a specific storage backend;
- direct dependence on external channel semantics as source of truth;
- direct mutation of irrecoverable state without confirmation.

## Boundary 2: Operational Core

This boundary owns the persistent operational meaning of Yarvis.

Includes:
- Organization;
- Person;
- Case;
- Conversation;
- ConversationMessage;
- IntakeItem;
- Checklist;
- RequirementFulfillment;
- OperationalAlert;
- NextActionSuggestion;
- DomainEvent.

Permitted dependencies:
- Evidence and Documents for linked artifacts;
- Identity and Relationships for actor and organization validation;
- Trust and Security for authorization, confirmation, retention, and audit policy;
- Infrastructure and Integrations through abstractions only.

Prohibited dependencies:
- UI components;
- direct storage implementation details;
- concrete AI providers;
- external automation tools as business logic source;
- any circular dependency on presentation layers.

## Boundary 3: Evidence and Documents

This boundary manages durable artifacts, their metadata, and their relation to the operational core.

Includes:
- documents;
- evidence;
- versions;
- validity;
- extracted text;
- classification metadata;
- storage references.

Permitted dependencies:
- Operational Core for case and checklist linkage;
- Identity and Relationships for remit and ownership;
- Trust and Security for access, retention, and validation policy;
- Infrastructure and Integrations for object storage adapters.

Prohibited dependencies:
- storing binary data directly in domain entities;
- treating folder structure as source of truth;
- direct coupling to a single provider's file format or storage semantics;
- business rules that bypass case context.

## Boundary 4: Identity and Relationships

This boundary describes who or what participates in the system and how that participation is recognized.

Includes:
- organizations;
- people;
- contact points;
- roles;
- relationship metadata.

Permitted dependencies:
- Operational Core for association to cases and intake;
- Trust and Security for access control and identity policy;
- Infrastructure and Integrations for authentication sources.

Prohibited dependencies:
- hard-coding business process logic into identity records;
- making relationships the owner of operational state;
- coupling identity to any particular communication channel.

## Boundary 5: Intelligence

This boundary includes AI-assisted interpretation, suggestion, summarization, and extraction.

Permitted dependencies:
- Interaction / Intake as the input surface;
- Operational Core as the source of truth for actions and state;
- Evidence and Documents for grounded context;
- Trust and Security for disclosure and confirmation rules;
- Infrastructure and Integrations for provider adapters.

Prohibited dependencies:
- AI as source of truth;
- irreversible domain mutation without confirmation;
- direct persistence of AI output as authoritative state without domain validation;
- leaking documents or sensitive data to providers without explicit policy approval.

## Boundary 6: Trust and Security

This boundary defines the rules that protect information, actions, and system continuity.

Includes:
- authentication;
- authorization;
- confirmation flows;
- retention policy;
- auditing policy;
- privacy controls;
- approval gates for sensitive actions.

Permitted dependencies:
- all other boundaries, but only through explicit policy and access control;
- Infrastructure and Integrations for secret management and backup tooling.

Prohibited dependencies:
- storing credentials in source control;
- bypassing authorization for convenience;
- exposing evidence or documents to third parties without policy and consent;
- allowing irreversible actions without human confirmation.

## Boundary 7: Infrastructure and Integrations

This boundary contains the technical adapters that make Yarvis run.

Includes:
- PostgreSQL;
- Alembic;
- object storage;
- email or channel connectors in the future;
- local development services;
- third-party integrations.

Permitted dependencies:
- all domain boundaries through interfaces and application services;
- external providers through adapters only.

Prohibited dependencies:
- owning business rules;
- becoming the source of truth;
- introducing hard-coded assumptions that cannot be swapped.

## Dependency Rules

- Interaction / Intake may depend on Operational Core, Evidence and Documents, Identity and Relationships, Intelligence, Trust and Security, and Infrastructure and Integrations.
- Operational Core may depend on Evidence and Documents, Identity and Relationships, and Trust and Security.
- Evidence and Documents may depend on Identity and Relationships, Trust and Security, and Infrastructure and Integrations.
- Intelligence may depend on Interaction / Intake, Operational Core, Evidence and Documents, Trust and Security, and Infrastructure and Integrations.
- Trust and Security may observe and constrain all other boundaries.
- Infrastructure and Integrations must never become the owner of domain decisions.

## Future Concepts Not Yet Approved for the MVP

The following concepts may remain useful for later phases, but they are not part of the approved MVP model:

- Relationship;
- Project;
- Dossier;
- Action;
- Commitment;
- Dependency;
- AuditRecord.

They may be referenced as future candidates, but they should not be treated as current persistent commitments in the approved MVP scope.

## Sprint 7.2 Boundary Note

- Observation Engine is a cross-cutting operational memory capability between Evidence/Documents and Operational Core.
- Policy evaluation consumes resolved operational facts and never executes dynamic user code.
- Mission Control consumes attention outputs from policy evaluations and conflicts, not raw source payloads.

