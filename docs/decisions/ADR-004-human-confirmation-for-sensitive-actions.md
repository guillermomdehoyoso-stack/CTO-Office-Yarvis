# ADR-004: Confirmación humana para acciones sensibles

- Status: Accepted
- Date: 2026-07-10

## Context
Yarvis puede proponer acciones y ejecutar tareas autorizadas, pero algunas acciones tienen alto impacto y deben permanecer supervisadas.

## Decision
Acciones sensibles como pagos, compras, contratos, facturas definitivas y comunicaciones de alto impacto requerirán confirmación humana o una política explícita.

## Consequences
- Se reduce el riesgo operativo y legal.
- Se mantiene el principio de supervisión humana.
- La arquitectura debe soportar flujos de aprobación explícitos.
