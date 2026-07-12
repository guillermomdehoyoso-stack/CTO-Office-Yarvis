# ADR-005: Integrar antes que reemplazar

- Status: Accepted
- Date: 2026-07-10

## Context
Existen herramientas maduras como WhatsApp, Gmail, Google Drive, OpenSolar, Salesforce, Mifiel y sistemas contables que ya resuelven funciones operativas específicas.

## Decision
Yarvis integrará estas herramientas cuando aporten valor y reduzcan riesgo, en lugar de reemplazarlas prematuramente.

## Consequences
- La arquitectura debe incluir adaptadores y puntos de integración claros.
- Se evita la construcción de funciones ya resueltas por herramientas maduras.
- La complejidad de integración queda pospuesta hasta que sea necesaria.
