# ADR-001: El Caso como núcleo operativo

- Status: Accepted
- Date: 2026-07-10

## Context
Yarvis debe operar sobre contexto y compromisos, no solo sobre tareas. La unidad operativa debe ser capaz de agrupar documentos, requisitos, decisiones, acciones y dependencias.

## Decision
Se adoptará el Caso como la unidad operativa central del dominio.

## Consequences
- El modelo de negocio se centra en Casos.
- El flujo de trabajo y la auditoría se organizan alrededor de cada Caso.
- La arquitectura de datos y la interfaz deben soportar Casos como raíz de operaciones.
