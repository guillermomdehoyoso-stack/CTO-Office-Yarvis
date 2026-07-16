# Yarvis Commercial Hierarchy and Operational Ownership v1.0

## 1. Purpose

This document defines how Yarvis represents commercial relationships, legal entities, physical locations, operational stores, and assets.

It establishes a shared architecture to ingest fragmented observations and attach them to the correct operational level without forcing premature persistence design.

## 2. Core Hierarchy

Approved NetPay hierarchy and reference ownership architecture:

ClientAccount
-> Company
-> Branch
-> Store
-> Asset

This is the approved NetPay hierarchy and the reference architecture for operational ownership. It is not a rigid assumption for every domain and can be adapted with explicit domain rules.

## 3. Entity Definitions

### ClientAccount

Commercial account relationship with a provider, distributor, or platform.

Examples:
- client_id
- commercial_owner
- distributor
- platform
- segment

### Company

Legal entity that may hold fiscal and contractual obligations.

Examples:
- rfc
- legal_name
- tax_regime
- fiscal_address

### Branch

Physical establishment or operating site.

Examples:
- branch_name
- address
- city
- state
- postal_code
- phone

### Store

Operational transaction/product account in a platform.

Examples:
- store_id
- product_type
- status

A store can be TPV, ecommerce, payment_link, or another provider-specific product.

### Asset

Physical or technical resource managed operationally.

Examples:
- serial_number
- model
- manufacturer
- platform_identifier

### ServiceCase

Operational or external support case tied to one or more hierarchy levels.

### Shipment

Logistics movement with destination, recipient, and delivery lifecycle.

### SalesSnapshot

Period-based activity record attached primarily to store and aggregable upward.

### Document

Binary or metadata-backed document linked to hierarchy levels with provenance.

### Checklist

Operational completion structure that can belong to company, branch, store, or asset contexts.

### Alert

Operational signal requiring attention, prioritization, and explicit handling.

### DomainEvent

Auditable immutable record of relevant domain transitions.

## 4. Relationship Cardinality

- ClientAccount 1:N Company
- Company 1:N Branch
- Branch 1:N Store
- Store 1:N Asset assignments over time
- Store 1:N SalesSnapshot
- Store 1:N ServiceCase
- ServiceCase 1:N Shipment when applicable
- any OperationalNode 1:N Documents / Evidence / Events / Alerts

A current asset assignment is not the same as asset assignment history.

## 5. NetPay Example

Client ID 970
|-- Company A - RFC AAA010101AAA
|   |-- Branch Metepec
|   |   |-- Store 503218 - TPV
|   |   |   |-- Asset A920-XYZ123
|   |   |   |-- SalesSnapshot
|   |   |   |-- ServiceCase CAS-12345
|   |   |   \-- Shipment 784563221
|   |   \-- Store 503219 - eCommerce
|   \-- Branch Toluca
|       \-- Store 503220 - TPV
\-- Company B - RFC BBB020202BBB
    \-- Branch Queretaro
        |-- Store 504100 - TPV
        \-- Store 504101 - Payment Link

This example shows:
- one Client ID has two Companies;
- one Company has several Branches;
- one Branch has several Stores;
- not every Store requires a terminal;
- one Asset may change Store over time.

## 6. Operational Ownership

Current assignment, historical assignment, physical location, logistics destination, and commercial ownership are separate facts.

Operational ownership chain:

Asset -> Store -> Branch -> Company -> ClientAccount

Each relation can change over time and must preserve history.

## 7. Recipient and Destination Separation

Yarvis must model these concepts independently:

- Email Recipient
- Operational Recipient
- Logistics Recipient
- Physical Destination
- Confirmed Operational Owner

No automatic equivalence is allowed between them.

## 8. Data Intake and Consolidation

Files and operational sources such as:

- client status tables;
- inventory reports;
- distributor development reports;
- operations reports;
- weekly sales;
- monthly sales;
- inactive stores;
- profitability reports;
- shipment guides;
- service case emails;

must become observations attached to hierarchy levels.

Each import must preserve:

- source_filename;
- file_hash;
- report_date;
- imported_at;
- field_level_provenance;
- confidence;
- confirmation_status.

Reports must not overwrite confirmed data blindly.

## 9. Document Organization

Logical document tree:

ClientAccount
|-- Commercial Documents
|-- Companies
|   |-- Fiscal Documents
|   \-- Branches
|       |-- Branch Documents
|       \-- Stores
|           |-- Onboarding Checklist
|           |-- Operational Documents
|           |-- Assets
|           |-- Shipments
|           |-- Cases
|           \-- Sales Reports

Physical storage may use Google Drive or another repository later. Yarvis stores metadata and relationships.

## 10. Checklist Ownership

### Company Checklist

- rfc;
- legal_representative;
- bank_account;

## Sprint 7.2 Note

Hierarchy assignment decisions now consume confirmed observations and resolution decisions before policy-driven attention is generated.
- fiscal_documentation.

### Branch Checklist

- address;
- proof_of_address;
- photos;
- local_contact.

### Store Checklist

- product;
- activation;
- store_id;
- operational_validation;
- first_transaction.

### Asset Checklist

- serial;
- assignment;
- shipment;
- delivery;
- activation;
- recovery.

## 11. Sales and Activity

Reference variables:

- sales_volume_current;
- sales_volume_previous;
- sales_volume_average_30d;
- sales_volume_average_90d;
- transaction_count;
- last_activity_at;
- inactive_days;
- sales_drop_percentage;
- criticality_score;
- churn_status.

These variables are architectural definitions only and are not implemented in this increment.

## 12. Churn Policy

Initial configurable policy:

- watch threshold: configurable;
- churn candidate threshold: 60 inactive days;
- cancellation requires human approval;
- high-volume stores may become critical earlier;
- recent shipment, replacement, open case, seasonality, or incomplete reports may suspend churn recommendation;
- assets should be reviewed for recovery before cancellation.

Suggested states:

- active
- watch
- churn_candidate
- cancellation_review
- cancelled
- recovered

All names remain in English in architecture and code.

## 13. Critical Store Detection

Criticality should consider:

- historical sales volume;
- recent sales decline;
- inactivity;
- revenue contribution;
- assigned asset cost;
- open service cases;
- missing data;
- data confidence.

Use deterministic and explainable policies first.

No machine learning yet.

## 14. OperationalNode

OperationalNode is an architectural interface/concept.

Possible fields:

- node_type;
- node_id;
- display_name;
- status;
- criticality;
- alerts;
- next_actions;
- timeline;
- checklist_progress;
- data_confidence.

No persistent generic table is introduced in this sprint.

## 15. Mission Control Guidance

Mission Control should surface:

- critical stores;
- churn candidates;
- assets to recover;
- missing store_id;
- missing asset serial;
- unresolved client_id;
- conflicting rfc;
- pending files;
- open service cases;
- unresolved shipments;
- incomplete checklists;
- high-value sales deterioration.

Mission Control should prioritize exceptions and next actions rather than generic charts.

## 16. Domain Ownership

### Data Intake

Captures files, emails, documents, and messages.

### Parser / Document Intelligence

Extracts observations.

### Identity Resolution

Proposes entity matches.

### Commercial Hierarchy

Defines where the observation belongs.

### Domain Engine

Applies confirmed relationships and state transitions.

### Mission Control

Surfaces attention and next actions.

### Document Repository

Stores binaries externally in the future.

### PostgreSQL

Stores normalized facts, observations, relationships, provenance, policies, and events.

## 17. Future Persistence Candidates

Registered without implementation:

- ClientAccount
- Company
- Branch
- Store
- Asset
- AssetAssignment
- SalesSnapshot
- OperationalNode projection
- ChurnPolicy
- CriticalityPolicy
- DocumentRepositoryReference

## 18. Non-goals

Do not implement now:

- generic hierarchy tables;
- graph database;
- churn engine;
- profitability engine;
- direct NetPay integration;
- automatic cancellation;
- browser automation;
- automatic asset reassignment;
- Google Drive repository;
- WhatsApp;
- Gmail OAuth;
- frontend changes;
- migrations.

## 19. Acceptance Rules

- Client ID != Company;
- Company != Branch;
- Branch != Store;
- Store != Asset;
- eCommerce Store may have no physical Asset;
- Asset assignment is historical;
- Shipment destination != confirmed ownership;
- data from reports is observation;
- confirmed data wins;
- provenance is mandatory;
- cancellation always requires human approval.
