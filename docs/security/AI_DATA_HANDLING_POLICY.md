# AI Data Handling Policy — Initial Classification

Status: Active baseline for local-first stage.

## 1. Purpose

Define what data can be sent to external AI providers, what requires redaction/consent, and what must remain local.

This policy does not claim local model processing exists today.

## 2. Data Classes

### Public

Examples:

- public commercial materials;
- public manuals;
- open catalogs.

Rules:

- External AI provider allowed: Yes.
- Redaction required: No.
- Consent required: No.
- Must process locally: No.
- Retention: short operational retention.
- Logging: summary metadata allowed.

### Internal

Examples:

- internal procedures;
- non-public source code;
- operational notes without sensitive personal data.

Rules:

- External AI provider allowed: Conditional.
- Redaction required: Recommended.
- Consent required: Not usually, unless policy requires.
- Must process locally: Preferred when possible.
- Retention: minimal required for operation.
- Logging: metadata only; no raw full content in logs.

### Confidential

Examples:

- contracts;
- quotations;
- client emails;
- operational financial data.

Rules:

- External AI provider allowed: Only with explicit approval and documented need.
- Redaction required: Yes, mandatory.
- Consent required: Yes, where legal/contractual basis applies.
- Must process locally: Preferred.
- Retention: strict minimum and documented purpose.
- Logging: no raw payload; only references and decision trace.

### Restricted

Examples:

- INE;
- bank statements;
- bank account data;
- credentials;
- sensitive tax data;
- legal acts and labor-sensitive documents;
- critical trade secrets.

Rules:

- External AI provider allowed: No by default.
- Redaction required: Yes, if any processing is approved.
- Consent required: Mandatory if exceptional handling is approved.
- Must process locally: Yes, or do not process with AI.
- Retention: strongest controls and shortest justified duration.
- Logging: never log raw content, credentials, or full identifiers.

## 3. Provider Usage Guardrails

- Do not send secrets, keys, tokens, credentials, or private connection strings.
- Do not send Restricted data to external AI providers by default.
- Do not claim local AI processing exists unless implemented and validated.
- Keep auditable records of what class was processed and under which approval.

## 4. Logging Rules

- No token/secret logging.
- No document full-body logging for Confidential/Restricted classes.
- Use IDs and hashes where traceability is needed.
- Separate technical logs from domain audit trails.

## 5. Review Trigger

This policy must be reviewed before:

- first external AI provider integration;
- first processing of customer sensitive documents;
- any production deployment.
