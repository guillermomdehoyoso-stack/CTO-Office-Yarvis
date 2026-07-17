# ADR-012: Operational Memory as a First-Class Domain

- Status: Accepted
- Date: 2026-07-16

## Context

Operational evidence is naturally fragmented across systems, documents, and communication channels. Evidence Consolidation organizes and preserves individual pieces of evidence, but long-term operational effectiveness requires persistent memory of how those pieces relate over time.

Operational Memory is not merely stored information. It is the continuously evolving contextual understanding of an operation.

## Decision

Yarvis adopts Operational Memory as a first-class architectural domain.

Operational Memory preserves:

- operational context;
- relationships between evidence;
- historical continuity;
- confirmations;
- provenance;
- unresolved conflicts; and
- operational timelines.

Operational Memory does not replace source systems. It continuously enriches their operational understanding by connecting their evidence.

## Principles

### Memory is cumulative

Knowledge grows; it is never recreated from scratch.

### Memory is explainable

Every remembered fact must be traceable to evidence.

### Memory is contextual

Information has little value without relationships. Context is part of memory.

### Memory evolves

Human confirmations improve memory. New evidence updates memory. History is never silently overwritten.

### Memory precedes intelligence

Observation precedes automation. Memory precedes recommendations. Recommendations precede autonomous actions.

### Memory emerges from real work

Operational Memory is enriched exclusively through real operational evidence, human confirmations, and validated observations. Artificial or speculative knowledge must never be introduced solely to satisfy an architectural design.

## Relationship with ADR-011

ADR-011 defines how evidence enters Yarvis. ADR-012 defines what Yarvis becomes after consolidating that evidence. Both decisions are complementary.

## Non-goals

Operational Memory is not:

- a CRM;
- an ERP;
- a document repository;
- a database backup; or
- a replacement for operational systems.

## Expected Consequences

Every future module must answer: **How does this enrich Operational Memory?** If it does not, it probably does not belong in Yarvis.

## Mission

Yarvis does not aim to become the place where operational work is performed. It aims to become the trusted operational memory that continuously organizes, connects, and preserves operational evidence, enabling humans to operate with clarity, continuity, and confidence.

## North Star

**Yarvis remembers what humans should not have to.**
