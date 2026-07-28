# WS-005B — Mission Event Timeline Frontend

**Status:** Implemented Engineering Increment — pending validation

## Purpose

WS-005B exposes the operational clock inside the existing Mission Work Item detail. It consumes the governed, tenant-scoped Timeline API; it does not create a separate work surface or reinterpret Event Store evidence.

## Operator Experience

The Work Item detail loads timeline records in their backend-provided sequence order. Each record presents a readable event label, localized date and time, exact timestamp on the time element, actor when available, and an evidence-derived description. Known lifecycle events show transitions for status, priority, and assignment. Unknown event types remain visible through a safe fallback rather than being omitted or guessed.

## Event Store and Timeline

The Event Store remains the append-only backend evidence authority. This frontend Timeline is only its operator-oriented representation. Payloads are rendered conservatively: fields that are not present are shown as unavailable rather than inferred.

## Internal Comments

An operator with the existing `mission.work.create` authority may append an internal comment through the public comment endpoint. Empty comments and duplicate submissions are prevented. On success the text is cleared and the Timeline is refreshed. On failure the captured text is retained and a governed error is shown. Editing and deletion are not provided.

## Multi-Organization Behavior

The component reuses the existing Mission Work access context and public API client. Organization identity and authority remain transport concerns owned by the existing client; the frontend neither derives organization data nor bypasses backend `404` concealment.

## Deferred Scope

AI, SLA, alerts, automation, attachments, external events, Timeline filters, comment editing or deletion, and broad visual redesign are outside WS-005B.
