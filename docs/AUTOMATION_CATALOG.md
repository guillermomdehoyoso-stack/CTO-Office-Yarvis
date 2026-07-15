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
