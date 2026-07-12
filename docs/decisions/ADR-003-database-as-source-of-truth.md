# ADR-003: La base de datos como fuente de verdad

- Status: Accepted
- Date: 2026-07-10

## Context
Las carpetas y archivos son vistas humanas del trabajo, pero no son suficientes para sostener contexto operativo, trazabilidad y reutilización de datos.

## Decision
La base de datos será la fuente de verdad operativa. El almacenamiento documental será un repositorio de archivos asociado a registros del dominio.

## Consequences
- Se evita el problema de la información dispersa en carpetas.
- El sistema puede reconstruir contexto, auditoría y asociación de documentos.
- Se requiere una capa de metadatos y una estrategia de almacenamiento consistente.
