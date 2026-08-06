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

Contacto solicitante por requisición, también propuesto y no implementado:

- `requester_contact_id`, `requester_name`, `requester_phone`,
  `requester_email`, `requester_role`, `source_channel` y
  `preferred_contact_channel` pertenecen a la requisición; el solicitante
  externo no es necesariamente el contacto principal del comercio ni el
  responsable interno;
- un comercio puede tener múltiples contactos y una persona puede originar
  múltiples requisiciones;
- `request_received_at` sigue siendo la fecha/hora efectiva de recepción;
- la futura búsqueda debe cubrir nombre, teléfono y correo del solicitante;
- el diseño futuro debe conservar referencia al contacto y una instantánea
  histórica mínima de sus datos al recibir la solicitud;
- teléfono y correo son PII: requieren aislamiento organizacional, acceso
  autorizado y exclusión de logs y eventos innecesarios.

NETPAY INTERNAL SUPPORT ROUTING, también propuesto y no implementado, distingue
expresamente `requester_contact` (persona externa que originó la requisición),
`internal_owner` (persona de nuestra operación responsable de su avance) y
`netpay_support_contact` (contacto o área interna de Netpay que puede apoyar
su resolución). Derivar a Netpay no transfiere ni elimina al `internal_owner`.

El futuro directorio de apoyo Netpay requiere `support_contact_id`, `name`,
`team_or_area`, `role`, `corporate_email`, `corporate_phone`,
`preferred_channel`, `supported_products`, `supported_request_types`,
`applicable_region_or_segment`, `backup_contact_id`, `availability_notes` y
`active_status`. Un contacto puede cubrir varios productos o tipos de
requerimiento, y debe conservar contacto principal y suplente cuando estén
disponibles.

El futuro registro de derivación requiere `referral_id`, `request_id`,
`support_contact_id` o `support_area`, `referred_at`, `referral_reason`,
`information_shared`, `external_ticket_reference`, `expected_response_at`,
`referral_status`, `last_followup_at`, `next_followup_at`, `responded_at`,
`resolved_at`, `escalation_level` y `response_summary`. Una requisición puede
tener varias derivaciones y escalaciones; debe conservarse el historial de
contactos y áreas involucradas.

La sugerencia futura de enrutamiento se basará sólo en mappings controlados,
nunca exclusivamente en conversaciones históricas. No enviará información o
documentos automáticamente sin confirmación; minimizará PII y documentos según
el tipo de atención; y excluirá teléfonos, correos, documentos y contenido
sensible de logs y eventos. La UI futura mostrará responsable interno, estado
“Esperando a Netpay”, contacto o área de apoyo, tiempo esperando respuesta,
próximo seguimiento y nivel de escalamiento.

NETPAY ATTENTION FOLIOS AND LOGISTICS TRACKING, también propuesto y no
implementado, distingue `request` (necesidad operativa del comercio),
`attention_folio` (identificador emitido por proceso o área interna de Netpay),
`logistics_movement` (envío, recolección, sustitución o devolución física) y
`tracking_guide` (número de guía emitido por el transportista). Una guía no
sustituye al folio ni a la requisición.

El futuro folio de atención requiere `attention_folio_id`, `folio_number`,
`request_id`, `process_type`, `product_type`, `netpay_area`,
`netpay_support_contact_id`, `opened_at`, `current_status`, `last_status_at`,
`last_verified_at`, `next_followup_at`, `resolved_at`, `resolution_summary` y
`evidence_reference`. Una requisición puede tener múltiples folios; su
existencia no significa resolución. Debe distinguirse estado reportado por
Netpay de último estado verificado, calcular antigüedad del folio y tiempo sin
actualización, y conservar al `internal_owner` como responsable de seguimiento.

El futuro movimiento logístico requiere `logistics_movement_id`, `request_id`,
`attention_folio_id` opcional, `movement_type`, `carrier`, `tracking_number`,
`origin`, `destination`, `generated_at`, `shipped_or_collected_at`,
`expected_delivery_at`, `delivered_at`, `logistics_status`,
`delivery_evidence_reference` y `exception_summary`. Un folio puede tener cero,
uno o múltiples movimientos; generar guía no prueba envío, recolección ni
entrega. Deben registrarse incidencias de entrega, rechazo, extravío o dirección
incorrecta.

Para altas debe poder registrarse y monitorearse cada etapa sin asumir que emitir
un folio equivale a activación. Para terminales debe conservarse
`terminal_serial_number` cuando aplique; para rollos e insumos, `quantity`;
ambos junto a `equipment_or_supply_type` y `operational_purpose`.

La UI futura mostrará folio, proceso, estado, antigüedad, última actualización,
espera de Netpay, guía y transportista, estado logístico y próximo seguimiento.
Folios, teléfonos, correos, domicilios, guías y números de serie requieren
aislamiento organizacional, minimización de PII y exclusión de logs/eventos no
necesarios. No se permite scraping ni consulta automática de portales Netpay o
transportistas sin autorización separada.

No se permite inferir RFC ni fechas reales, ni ejecutar backfill, hasta definir
el tratamiento de datos históricos, la normalización y unicidad del RFC, el
tratamiento de solicitudes cuya fecha de recepción sea desconocida o cuyos
contactos sean incompletos. La futura autorización deberá evaluar PII,
aislamiento organizacional, contratos/endpoints afectados y su relación con
F-011 sin realizar cutover de identidad u organización.

### EPIC-PROC-001 — Supplier Catalog Intelligence
- Consultar DM Solar.
- Consultar Exel Solar.
- Comparar precio y disponibilidad.
- Solicitar despiece al vendedor.
- Cargar cotización recibida.
- Comparar cotización formal contra precio en línea.
- Calcular impacto en margen.
