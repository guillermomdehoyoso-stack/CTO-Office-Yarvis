# Yarvis Operating Model v1.0

## 1. Purpose

Yarvis is not a chatbot and it is not a CRM.

Yarvis is an Operating System for the founder and for the day-to-day operation of the company. Its purpose is to amplify the founder's ability to decide, coordinate, and execute with speed, clarity, and traceability.

The system exists to reduce friction in the operational layer of the business, keep work grounded in real cases, and preserve context as durable operational memory.

## 2. Core Principles

The following principles are permanent design constraints for Yarvis:

- Domain First: the domain model leads implementation decisions, not the other way around.
- AI is replaceable: intelligence can be swapped, upgraded, or removed without rewriting the domain.
- Conversations are channels, not the product: conversation is a means of intake and coordination, not the center of the system.
- Mission Control is the Operating System: the primary surface of the product is the operational workspace, not a chat window.
- Cases are the operational backbone: work is organized around cases, not around loose messages or tasks.
- Everything becomes operational memory: relevant inputs, decisions, and events should persist as traceable memory.
- Time is a first-class domain concept: ordering, deadlines, validity, and recurrence are core concerns.
- Human confirmation before irreversible actions: sensitive or irreversible actions require explicit confirmation.
- Modular Monolith First: the system should evolve as a well-structured monolith before any distributed architecture is considered.
- Inbox First: incoming work must be captured, triaged, and contextualized before being transformed into execution.
- Build capabilities that pay for themselves: each major capability should create measurable operational value.

## 3. Four Dimensions of Yarvis

Yarvis is organized around four dimensions that define how operational work is understood and executed.

- Space: where the work belongs. This includes organizations, people, cases, projects, and the operational surfaces that hold work together.
- Time: when the work matters. This includes received time, validity windows, due dates, sequencing, waiting periods, and recency.
- Context: why the work matters. This includes the case, the organization, the person, the source of the intake, and the associated intent.
- Memory: what the system must retain. This includes messages, events, evidence, confirmations, and prior decisions.

These four dimensions should remain visible in every future product decision.

## 4. Domain Language

The domain vocabulary is deliberately explicit. It should remain stable and shared across product, engineering, and operations.

- Organization: the company, client, partner, or external entity around which work is organized.
- Person: the human contact connected to an organization or a case.
- Mission: the future top-level unit of strategic intent. Mission is a future principal entity and is not implemented yet.
- Case: the operational backbone that groups work, evidence, state, and decisions.
- Conversation: a channel for intake, clarification, and operational coordination.
- Message: a single unit of conversation content; it is raw material, not the final domain object.
- Intake: the normalized entry point for work received from a conversation or other channel.
- Evidence: a captured artifact or factual reference associated with a case or intake.
- Checklist: the structured set of requirements needed to advance a case.
- Requirement: an individual condition that must be fulfilled or reviewed.
- Fulfillment: the recorded satisfaction, rejection, or not-applicable outcome for a requirement.
- Alert: a condition that requires attention because a case has risk, blockage, expiration, or missing evidence.
- Suggestion: a proposed next action generated from operational state.
- Domain Event: an auditable record of something that happened in the system.

Mission should be treated as the future main strategic entity, but not as a current implementation dependency.

## 5. Conversation Model

The conversation model is intentionally progressive.

Conversation

Messages

Intent

Entities

Actions

Domain Events

A message is only the starting material. It should be interpreted, contextualized, and converted into operational meaning. The product should never confuse the raw message with the actual decision, action, or state transition it may trigger.

The system should evolve from conversation as input toward conversation as a structured operational interface.

## 6. Mission Control

Mission Control is not a dashboard.

It is the primary interface of the Operating System: the place where the founder sees, prioritizes, and acts on what matters now.

Mission Control should evolve to surface the operational reality of the company across the following areas:

- Inbox
- Attention
- Cases
- Projects
- Organizations
- People
- Calendar
- Waiting For
- Alerts
- Conversation
- Search

The design goal is not visual density for its own sake. The goal is to present actionable structure, current state, and next decisions in one coherent working surface.

## 7. Intelligence Layer

Intelligence must remain decoupled from the core domain.

The target architecture is:

UI
Conversation Service
AI Orchestrator
Domain Engine
Persistence

This separation exists for a reason. The UI should remain focused on interaction. The Conversation Service should coordinate intake and conversational state. The AI Orchestrator should interpret and enrich inputs. The Domain Engine should own business rules and state transitions. Persistence should store the resulting facts and events.

This layering ensures that Yarvis can replace AI providers, change orchestration strategies, or add intelligence capabilities without destabilizing the domain model or rewriting historical state.

## 8. Investment Philosophy

Yarvis must fund its own evolution.

Every new capability must either reduce operational cost, save founder time, reduce risk, or generate measurable revenue before it justifies larger investment. Features are not justified by novelty; they are justified by value.

The bootstrap strategy is therefore pragmatic:

- ship capabilities that remove manual work first;
- capture the resulting operational memory;
- use that memory to improve prioritization and decision quality;
- reinvest savings into the next capability layer;
- expand intelligence only after the operational foundation proves durable.

This keeps the system aligned with the company's capacity to absorb complexity and prevents premature platform overbuild.

## 9. Current Status

At the end of Block 6, Yarvis has a stable foundation and a working operational core.

The current state includes:

- Foundation: FastAPI, PostgreSQL, Alembic, Docker Compose, and a reproducible local environment.
- Operational Core: cases, organizations, people, events, and the core relational model.
- Evidence: capture and persistence of evidence records associated with cases and intake.
- Checklists: configurable requirements, fulfillments, and validation workflows.
- Alerts: operational alert generation, visibility, and case-level attention tracking.
- Mission Control: the main operational surface for summary and attention items.
- Conversation Workspace: a conversation-driven intake flow with context confirmation.
- React Frontend: a navigable UI for the main operating surfaces.
- Docker: local services for API, web, and PostgreSQL.
- PostgreSQL: durable source of truth for the domain.
- FastAPI: the public API surface and operational entry point.

This is a foundation, not the final form. It is sufficient to support the next phase of product evolution.

## 10. Next Phase

The next phase is no longer infrastructure.

It is Phase II — Intelligence.

The focus of Phase II will be to build the capabilities that turn operational memory into useful action:

- Conversation Orchestrator: structure conversational intake and route it into domain meaning.
- Inbox First: make incoming work visible, triageable, and actionable before it becomes execution debt.
- Operational Memory: strengthen the persistence and retrieval of decisions, context, and history.
- Founder Copilot: use the accumulated system state to help the founder decide and act faster.

Phase II should deepen intelligence without breaking the principles established in this model. The domain remains primary, and intelligence serves the operating system rather than replacing it.

## 11. Sprint 7.2 Addendum

The Observation Engine pipeline is approved as the reusable memory path:

Source -> Document -> Observation -> Identity Resolution -> Commercial Hierarchy -> Operational State -> Policy Evaluation -> Attention Item -> Mission Control.

Evidence is not operational truth and no source may bypass this pipeline.
