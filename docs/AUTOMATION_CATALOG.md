# Automation Catalog

## Purpose

Provide a canonical registry for future automations so Yarvis can scale without ad-hoc redesign.

## Required Record Shape

Each automation candidate must register:

- Name
- Trigger
- Inputs
- Outputs
- Confidence level
- Human confirmation required
- Data sources
- Domain owner
- Current mode: Observation, Demonstration, or Automation
- Guardrails
- Failure handling

## Initial Catalog Entries

### Gmail NetPay Inbox Hook
- Name: Gmail NetPay Inbox Hook
- Trigger: New NetPay-related email detected
- Inputs: message headers, normalized body, attachment metadata
- Outputs: normalized intake payload
- Confidence level: medium
- Human confirmation required: yes
- Data sources: Gmail API read-only (future)
- Domain owner: Operations Inbox
- Current mode: Observation
- Guardrails: no token in Git, no external AI payload transfer
- Failure handling: leave case pending investigation

### WhatsApp Intake Hook
- Name: WhatsApp Intake Hook
- Trigger: Incoming operational message
- Inputs: sender, body, media metadata
- Outputs: normalized intake payload
- Confidence level: low
- Human confirmation required: yes
- Data sources: WhatsApp provider (future)
- Domain owner: Interaction Intake
- Current mode: Observation
- Guardrails: no irreversible actions
- Failure handling: keep as raw intake candidate

### Google Drive Evidence Hook
- Name: Google Drive Evidence Hook
- Trigger: New file event in monitored folder
- Inputs: file metadata, storage reference
- Outputs: evidence candidate
- Confidence level: medium
- Human confirmation required: yes
- Data sources: Google Drive API (future)
- Domain owner: Evidence Documents
- Current mode: Observation
- Guardrails: metadata-only unless approved
- Failure handling: do not link automatically to case

### Portal NetPay Hook
- Name: Portal NetPay Hook
- Trigger: User-initiated retrieval
- Inputs: folio, tracking reference
- Outputs: operational updates proposal
- Confidence level: medium
- Human confirmation required: yes
- Data sources: Portal NetPay (future)
- Domain owner: NetPay Operations
- Current mode: Observation
- Guardrails: no browser automation in current phase
- Failure handling: manual reconciliation required

### Hoymiles Hook
- Name: Hoymiles Hook
- Trigger: Monitoring job window
- Inputs: site status signals
- Outputs: alert candidates
- Confidence level: medium
- Human confirmation required: yes
- Data sources: Hoymiles platform (future)
- Domain owner: Energy Operations
- Current mode: Observation
- Guardrails: no autonomous remediation
- Failure handling: alert-only

### APsystems Hook
- Name: APsystems Hook
- Trigger: Monitoring job window
- Inputs: inverter status signals
- Outputs: incident candidates
- Confidence level: medium
- Human confirmation required: yes
- Data sources: APsystems platform (future)
- Domain owner: Energy Operations
- Current mode: Observation
- Guardrails: no autonomous remediation
- Failure handling: alert-only

### OpenSolar Hook
- Name: OpenSolar Hook
- Trigger: Proposal/status update event
- Inputs: project metadata and status
- Outputs: case update proposal
- Confidence level: medium
- Human confirmation required: yes
- Data sources: OpenSolar platform (future)
- Domain owner: Commercial Operations
- Current mode: Observation
- Guardrails: no write-back without approval
- Failure handling: pending review queue

## Commercial Hierarchy Data Operations (Documentation-Only)

### Import Client Status Report
- Trigger: Manual report import request
- Input: client_status_report file
- Output: client_account and company observation candidates
- Approval requirement: human confirmation required
- Source: operational reports
- Future status: planned

### Import Inventory Report
- Trigger: Manual report import request
- Input: inventory_report file
- Output: store and asset observation candidates
- Approval requirement: human confirmation required
- Source: inventory operations reports
- Future status: planned

### Import Distributor Development Report
- Trigger: Manual report import request
- Input: distributor_development_report file
- Output: client_account commercial relationship observations
- Approval requirement: human confirmation required
- Source: distributor development reports
- Future status: planned

### Import Operations Report
- Trigger: Manual report import request
- Input: operations_report file
- Output: service_case, shipment, and ownership observations
- Approval requirement: human confirmation required
- Source: operations reports
- Future status: planned

### Import Weekly Sales Report
- Trigger: Scheduled weekly import window
- Input: weekly_sales_report file
- Output: sales_snapshot candidates by store
- Approval requirement: human confirmation required
- Source: weekly sales reports
- Future status: planned

### Import Monthly Sales Report
- Trigger: Scheduled monthly import window
- Input: monthly_sales_report file
- Output: sales_snapshot candidates by store and branch aggregate
- Approval requirement: human confirmation required
- Source: monthly sales reports
- Future status: planned

### Detect Inactive Stores
- Trigger: Daily inactivity evaluation window
- Input: sales_snapshot history and last_activity_at
- Output: inactivity observations and watch recommendations
- Approval requirement: human confirmation required
- Source: consolidated sales snapshots
- Future status: planned

### Detect Critical Stores
- Trigger: Daily criticality evaluation window
- Input: sales trend, inactivity, open cases, asset cost, data confidence
- Output: criticality recommendations
- Approval requirement: human confirmation required
- Source: hierarchy and operational telemetry
- Future status: planned

### Recommend Asset Recovery
- Trigger: churn_candidate or cancellation_review recommendation
- Input: store inactivity, asset assignment history, open shipments/cases
- Output: asset_recovery recommendation
- Approval requirement: human confirmation required
- Source: hierarchy, shipments, and service cases
- Future status: planned

### Prepare Cancellation Review
- Trigger: churn_candidate threshold reached
- Input: inactivity window, revenue impact, exceptions, unresolved conflicts
- Output: cancellation_review package
- Approval requirement: human confirmation required
- Source: sales snapshots, hierarchy, and policy rules
- Future status: planned

### Accounting Intake Observation Hook
- Trigger: Manual accounting intake import
- Input: invoice photo, PDF invoice, CFDI XML, issued/received invoices, payment complements, bank movements, expense receipts, tax retentions, manual adjustments
- Output: accounting observation candidates (issuer_rfc, receiver_rfc, uuid, invoice_date, subtotal, vat_amount, withheld taxes, total, period, source_document_hash)
- Approval requirement: human/accountant confirmation required
- Source: accounting evidence inputs
- Future status: planned
