# Architectural Risk Register

## R001 — Dependencia del Connector para contexto de negocio

**Estado**
Open

**Probabilidad**
Alta

**Impacto**
Alto

**Descripción**

Los conectores (Huawei, Solis, etc.) pueden no proporcionar toda la información necesaria para modelar correctamente el dominio de negocio (Owner, Project, Site, Asset ownership, MRV boundaries, etc.).

**Consecuencia**

Energy Tracer quedaría acoplado a la ontología del fabricante, dificultando:

- Multi-cliente
- Multi-fabricante
- Cambios de propietario
- Fusiones de plantas
- Auditoría
- Digital Evidence

**Mitigación propuesta**

Crear un Context Registry interno compuesto por:

- Organization
- Project
- Site
- Asset
- Asset Identifier
- Connector
- Data Stream

Los connectors únicamente aportan datos técnicos e identificadores externos.

**Owner**

CTO

**Sprint objetivo**

Sprint 06D

**Estado**

Open