# Backlog inicial

## P0
- Estructura del monolito modular.
- Docker Compose.
- PostgreSQL y migraciones.
- Entidades base de organización, personas y Casos.
- Documentos y almacenamiento.
- Checklists y cumplimiento.
- Estados, acciones y auditoría.

## P1
- Interfaz mínima.
- Datos de demostración.
- Pruebas de extremo a extremo.

## Futuro

### RADAR-REQ — Antigüedad y búsqueda fiscal

**NOT AUTHORIZED FOR IMPLEMENTATION.** Requerimiento pendiente del Radar
Operativo Netpay. Depende del cierre técnico y de la revisión humana de F-011
Slices A–D, y requiere una autorización separada antes de cualquier cambio de
modelo, migración, API, UI, fixture, prueba, backfill o cutover.

Alcance propuesto, no implementado:

- comercio: `commercial_name`, `legal_name` y RFC normalizado;
- solicitud: `request_received_at` independiente de `created_at`, `closed_at`
  para solicitudes cerradas y `target_at` conservado para vencimientos;
- búsqueda unificada por nombre comercial, razón social y RFC; RFC insensible a
  mayúsculas, espacios y guiones;
- días abierta calculados, nunca persistidos: fecha actual menos
  `request_received_at` para abiertas, o `closed_at` menos
  `request_received_at` para cerradas;
- orden predeterminado de solicitudes abiertas por antigüedad y UI con Comercio,
  RFC, Estado, Días abierta, Fecha de solicitud, Siguiente acción y Faltantes;
- `target_at` como dato secundario y fuente del indicador Vencidos.

No se permite inferir RFC ni fechas reales, ni ejecutar backfill, hasta definir
el tratamiento de datos históricos, la normalización y unicidad del RFC, y el
tratamiento de solicitudes cuya fecha de recepción sea desconocida. La futura
autorización deberá evaluar PII, aislamiento organizacional, contratos/endpoints
afectados y su relación con F-011 sin realizar cutover de identidad u
organización.

### EPIC-PROC-001 — Supplier Catalog Intelligence
- Consultar DM Solar.
- Consultar Exel Solar.
- Comparar precio y disponibilidad.
- Solicitar despiece al vendedor.
- Cargar cotización recibida.
- Comparar cotización formal contra precio en línea.
- Calcular impacto en margen.
