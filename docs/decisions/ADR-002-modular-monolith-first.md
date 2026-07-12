# ADR-002: Monolito modular como punto de partida

- Status: Accepted
- Date: 2026-07-10

## Context
El alcance inicial exige velocidad, claridad y control sin introducir complejidad innecesaria.

## Decision
Se implementará un monolito modular para el Foundation Sprint, con módulos internos claramente delimitados.

## Consequences
- Se reduce la complejidad operativa temprana.
- Se facilita la evolución a servicios si apareciera una necesidad real.
- La arquitectura debe mantener límites claros entre módulos del dominio e infraestructura.
