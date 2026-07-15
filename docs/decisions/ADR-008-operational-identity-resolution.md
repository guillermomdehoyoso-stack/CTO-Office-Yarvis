# ADR-008: Operational Identity Resolution

- Status: Accepted
- Date: 2026-07-14

## Context

Yarvis recibe información desde fuentes distintas:

- Gmail
- documentos
- guías de envío
- reportes
- Portal NetPay
- Salesforce
- WhatsApp
- Google Drive
- sistemas de monitoreo
- captura manual

Una misma entidad puede aparecer con identificadores distintos, incompletos, desactualizados o contradictorios.

Ejemplos:

- nombre comercial;
- razón social;
- RFC;
- correo;
- teléfono;
- domicilio;
- Store ID;
- Client ID;
- número de serie;
- número de guía;
- folio de soporte;
- nombre de sucursal;
- destinatario de envío.

El parser extrae candidatos, pero no debe ser responsable de decidir definitivamente qué entidad representan.

## Decision

Yarvis tendrá un concepto arquitectónico explícito llamado:

Operational Identity Resolution

Su responsabilidad será recibir observaciones provenientes de distintas fuentes y proponer relaciones con entidades operativas existentes.

La resolución deberá distinguir:

- Organization
- Person
- Client
- Branch
- Store
- Asset
- Shipment
- Service Case
- Conversation
- Intake
- Evidence

La resolución no convierte automáticamente un valor extraído en una identidad confirmada.

Debe conservar:

- valor observado;
- tipo de identificador;
- fuente;
- método de extracción;
- confianza;
- momento de observación;
- entidad candidata;
- estado de confirmación;
- usuario o proceso que confirmó.

Estados mínimos:

- observed
- candidate
- confirmed
- rejected
- superseded
- conflicted

Reglas obligatorias:

1. Los identificadores fuertes tienen mayor peso:
   - UUID interno;
   - Store ID;
   - Client ID;
   - número de serie;
   - RFC confirmado;
   - folio oficial.

2. Los identificadores débiles no deben resolver por sí solos:
   - nombre;
   - domicilio;
   - teléfono;
   - destinatario;
   - asunto de correo.

3. Un mismo valor puede pertenecer a varias entidades.

4. Una entidad puede tener múltiples identificadores históricos.

5. Los valores confirmados por una persona prevalecen sobre extracción automática.

6. OCR o IA nunca pueden sobrescribir silenciosamente un valor confirmado.

7. Los conflictos deben conservarse y volverse visibles.

8. La fuente original nunca debe perderse.

9. La resolución automática con baja confianza debe producir una sugerencia, no una mutación de dominio.

10. Toda unión o separación de identidades debe ser auditable.

## Asset terminology

El concepto general será Asset.

Una terminal NetPay es un tipo de Asset.

El código actual puede conservar temporalmente nombres como:

- NetpayDeviceAssignment
- device_serial
- devices

Estos nombres se consideran específicos del módulo NetPay y compatibles durante la transición.

No realizar renombrado de código o migraciones dentro de este ADR.

Una futura decisión podrá introducir una entidad general Asset cuando existan al menos dos dominios que requieran administración común de activos.

Ejemplos futuros:

- terminal NetPay;
- inversor;
- microinversor;
- medidor;
- cargador EV;
- módem;
- DTU;
- herramienta;
- equipo de instalación.

## Consequences

Positivas:

- reduce duplicados;
- conserva trazabilidad;
- permite integrar nuevas fuentes;
- mejora conciliación logística;
- permite corregir errores sin perder historia;
- desacopla parser de identidad;
- prepara el Operational Graph.

Costos:

- requiere confirmación humana inicial;
- aumenta la metadata;
- exige gestión explícita de conflictos;
- puede producir múltiples candidatos;
- requiere reglas específicas por dominio.

## Rejected Alternatives

1. Resolver por coincidencia exacta de texto.
2. Usar el parser como fuente de verdad.
3. Crear automáticamente organizaciones o sucursales.
4. Sobrescribir datos antiguos con la última observación.
5. Construir inmediatamente un knowledge graph externo.
6. Renombrar todo Device a Asset en este sprint.

## Status

Accepted.