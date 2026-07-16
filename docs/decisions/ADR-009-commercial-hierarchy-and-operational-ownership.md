# ADR-009: Commercial Hierarchy and Operational Ownership

- Status: Accepted
- Date: 2026-07-14

## Context

Yarvis must consolidate operational data from multiple reports, documents, emails, systems, and business lines.

For NetPay, the observed hierarchy is:

- one Client ID may contain several legal companies or RFCs;
- one Company may contain several physical Branches;
- one Branch may contain several Stores;
- one Store may have several Assets over time;
- Assets may move between Stores;
- Service Cases, Shipments, Documents, Sales Snapshots, Checklists, Alerts, and Events may belong to different levels of the hierarchy.

Therefore:

- Client ID is not equivalent to Company;
- Company is not equivalent to Branch;
- Branch is not equivalent to Store;
- Store is not equivalent to Asset;
- physical destination is not equivalent to operational ownership.

## Decision

Yarvis adopts the following commercial hierarchy:

ClientAccount
    1 --- N Company

Company
    1 --- N Branch

Branch
    1 --- N Store

Store
    1 --- N Asset over time

The approved conceptual hierarchy is:

ClientAccount
    |
    |-- Company
    |      |
    |      |-- Branch
    |      |      |
    |      |      |-- Store
    |      |      |      |-- Asset
    |      |      |      |-- ServiceCase
    |      |      |      |-- Shipment
    |      |      |      |-- SalesSnapshot
    |      |      |      |-- Checklist
    |      |      |      |-- Alert
    |      |      |      \-- Document / Evidence
    |      |
    |      \-- Contacts
    |
    \-- Commercial Relationship

## Definitions

### ClientAccount

Represents the commercial account or relationship maintained with a provider, platform, distributor, or business line.

For NetPay, the primary external identifier is:

- Client ID

A ClientAccount is not a legal company.

A ClientAccount may contain one or more Companies.

Possible metadata:

- Client ID;
- distributor;
- commercial owner;
- status;
- onboarding date;
- provider or platform;
- commercial segment.

### Company

Represents a legal entity.

Primary identifiers may include:

- RFC;
- legal name;
- tax regime;
- fiscal address;
- internal UUID.

A Company may belong to a ClientAccount.

A Company may have several Branches.

### Branch

Represents a physical establishment, operating location, or site.

Possible identifiers:

- branch name;
- address;
- city;
- state;
- postal code;
- phone;
- geolocation in the future;
- references.

A Branch may contain several Stores.

A Branch must not be confused with a Store.

### Store

Represents an operational record or product account where transactions or platform activity occur.

For NetPay, the strong identifier is:

- Store ID

A Store may represent:

- TPV;
- eCommerce;
- payment link;
- another NetPay product.

A Branch may contain several Stores.

A Store may exist without a physical Branch in cases such as eCommerce.

### Asset

Represents a physical or technical resource managed operationally.

Examples:

- NetPay terminal;
- PIN Pad;
- SmartPOS;
- router;
- scanner;
- solar inverter;
- microinverter;
- meter;
- DTU;
- modem;
- EV charger;
- battery;
- installation tool.

Possible identifiers:

- serial number;
- model;
- manufacturer;
- QR;
- platform identifier;
- internal UUID.

A NetPay terminal is a type of Asset.

Existing NetPay names such as:

- NetpayDeviceAssignment
- device_serial
- devices

may remain temporarily as module-specific terminology.

No renaming or migration is authorized in this ADR.

### ServiceCase

Represents an operational or external support case.

It may be associated with:

- ClientAccount;
- Company;
- Branch;
- Store;
- Asset;
- Shipment.

### Shipment

Represents a logistics movement.

It may link:

- origin;
- recipient;
- physical destination;
- Branch;
- Store;
- Asset;
- ServiceCase.

Shipment destination does not automatically determine confirmed operational ownership.

### SalesSnapshot

Represents activity measured for a period.

It should normally attach to a Store, while also supporting aggregation upward to:

- Branch;
- Company;
- ClientAccount.

## Operational Ownership

Operational ownership must be resolved independently from physical location.

The expected chain is:

Asset
    v assigned to
Store
    v belongs operationally to
Branch
    v belongs legally to
Company
    v belongs commercially to
ClientAccount

This chain may change over time.

Yarvis must preserve assignment history.

Examples:

- an Asset can be shipped but not yet assigned;
- an Asset can be delivered to a Branch but assigned later to a Store;
- an Asset can move from one Store to another;
- an eCommerce Store may have no physical Asset;
- one Branch may contain several Stores;
- one Company may operate several RFC-linked or operational records according to provider rules.

## OperationalNode Concept

Yarvis introduces OperationalNode as an architectural concept only.

OperationalNode is not yet a persistent entity.

Any level of the hierarchy may behave as an operational node:

- ClientAccount;
- Company;
- Branch;
- Store;
- Asset;
- ServiceCase;
- Shipment.

An OperationalNode may expose:

- status;
- timeline;
- documents;
- evidence;
- checklists;
- alerts;
- next actions;
- owner;
- criticality;
- data confidence.

Mission Control should be able to surface attention items from any OperationalNode without requiring a separate dashboard architecture for each entity type.

## Identity Resolution Order

Operational Identity Resolution should attempt to resolve:

1. ClientAccount by Client ID;
2. Company by confirmed RFC;
3. Branch by normalized physical identity;
4. Store by Store ID;
5. Asset by serial or strong identifier;
6. Shipment by tracking number;
7. ServiceCase by official folio.

The order does not imply that all levels must exist before downstream data can be captured.

Observations may remain unresolved.

## Strong Identifiers

Examples:

- internal UUID;
- Client ID;
- confirmed RFC;
- Store ID;
- Asset serial number;
- official Service Case folio;
- tracking number within a known carrier.

## Weak or Contextual Identifiers

Examples:

- commercial name;
- recipient name;
- approximate company name;
- address text;
- phone;
- email;
- OCR text;
- branch label;
- forwarded email subject.

Weak identifiers must not create definitive ownership on their own.

## Documents and Checklists

Documents may belong to different hierarchy levels.

Examples:

### ClientAccount

- commercial agreement;
- distributor relationship;
- account-level reports.

### Company

- tax certificate;
- RFC;
- bank statement;
- legal documents;
- power of attorney.

### Branch

- proof of address;
- photographs;
- local permits;
- site evidence.

### Store

- onboarding checklist;
- product activation;
- operational status;
- sales reports.

### Asset

- serial label;
- assignment;
- shipment;
- repair;
- replacement;
- collection evidence.

Yarvis must not force all documents into a single flat folder.

## Sales and Churn

Sales activity belongs primarily to Store.

Mission Control may aggregate sales to:

- Branch;
- Company;
- ClientAccount.

Initial policy concepts:

- watch after configurable inactivity;
- churn candidate after configurable inactivity;
- cancellation only after human approval;
- critical stores prioritized by historical sales volume and deterioration;
- high-value stores may require attention before reaching the churn threshold.

No churn engine is implemented in this ADR.

## Cross-Domain Generalization

NetPay example:

ClientAccount
    v
Company
    v
Branch
    v
Store
    v
Asset

Energia Fotonica example:

ClientAccount
    v
Company
    v
Site or Branch
    v
Plant or Project
    v
Asset

Asset examples in Energia Fotonica:

- inverter;
- microinverter;
- meter;
- gateway;
- battery;
- charger.

The hierarchy is intended to be reusable, but domain-specific concepts must not be forced prematurely into a single generic model.

## Consequences

Positive:

- reflects actual NetPay ownership structure;
- supports several RFCs under one Client ID;
- supports several Branches under one Company;
- supports several Stores under one Branch;
- supports Asset movement;
- enables document organization by level;
- supports consolidated reporting;
- enables Mission Control aggregation;
- supports churn and profitability later;
- provides a reusable structure across business lines.

Costs:

- requires explicit relationship management;
- introduces hierarchy ambiguity when reports are incomplete;
- requires historical assignments;
- may require future model migrations;
- requires conflict detection;
- increases metadata and provenance requirements.

## Rejected Alternatives

1. Treat Client ID as Company.
2. Treat RFC as ClientAccount.
3. Treat Store as physical Branch.
4. Attach Assets directly to Company only.
5. Flatten all data into a single merchant table.
6. Create a graph database immediately.
7. Introduce a generic Asset table before a second domain requires it.
8. Rename all NetPay Device code immediately.
9. Assume physical destination equals operational ownership.
10. Store all documents in a single folder per client.

## Status

Accepted.
