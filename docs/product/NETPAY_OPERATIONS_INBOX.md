# NetPay Operations Inbox

## Proposito

Habilitar un flujo operativo inicial para detectar correos NetPay con folio y guia, convertirlos en casos operativos y completar manualmente la investigacion para confirmar cliente, comercio, domicilio, Store ID y serie de terminal.

## Fuentes

- Correo normalizado importado manualmente en `POST /netpay/service-cases/import-email`.
- IntakeItem creado desde correo para trazabilidad.
- Confirmacion humana en `PATCH /netpay/service-cases/{id}/investigation`.
- Registro logistico adicional en `POST /netpay/service-cases/{id}/shipments`.
- Inventario de terminales en `GET /netpay/devices` y `GET /netpay/stores/{store_id}/devices`.

## Flujo

1. Importar correo normalizado con headers y cuerpo.
2. Parser detecta folio, guias y movimiento probable.
3. Se crea `NetpayServiceCase` en estado `pending` y shipments detectados.
4. El backend conserva candidatos por campo con confidence y provenance.
5. La investigacion manual confirma o rechaza cada dato operativo.
6. Se registra timeline de eventos de dominio para trazabilidad.

## Campos

### NetpayServiceCase

- id UUID
- folio unico
- received_at UTC
- case_type opcional
- status
- source_email_id opcional
- source_thread_id opcional
- source_subject
- source_sender opcional
- source_intake_item_id opcional
- customer_name opcional
- merchant_name opcional
- address opcional
- store_id opcional
- device_serial opcional
- movement_type: outbound, collection, unknown
- investigation_status: pending, in_progress, confirmed
- notes opcional
- recipient_addresses
- operational_recipient
- recipient_resolution_source
- recipient_resolution_confidence
- created_at
- updated_at

### NetpayShipment

- id UUID
- service_case_id FK
- tracking_number
- carrier opcional
- direction: outbound, collection, unknown
- status
- shipped_at opcional
- delivered_at opcional
- recipient_name, receiver_company, branch, address_full, city, state, postal_code, phone
- folio, store_id, device_serial
- created_at

### NetpayDeviceAssignment

- id UUID
- device_serial
- store_id opcional
- organization_id opcional
- assigned_at opcional
- returned_at opcional
- status
- service_case_id opcional
- created_at
- updated_at

## Reglas

- Idempotencia por `gmail_message_id` y por `folio`.
- El destinatario operativo se resuelve en orden: Delivered-To, X-Original-To, Original-Recipient, To, Cc, alias reenviado.
- `operational_recipient` no se infiere solo desde `To` si existen headers de mayor prioridad.
- Toda asociacion cliente/store/serie es propuesta hasta confirmacion humana.
- No se crean asociaciones definitivas con baja confianza.
- Email recipient, operational recipient y physical delivery destination se resuelven por separado.
- Cada campo extraido conserva value, confidence, provenance, source_reference y confirmation_status.
- La conciliacion operativa sigue [IDENTITY_RESOLUTION.md](../architecture/IDENTITY_RESOLUTION.md) y ADR-008 para preservar evidencia, candidatos y conflictos.

## API Backend 7.1A

- POST /netpay/import-email
- POST /netpay/import-document
- GET /netpay/service-cases
- GET /netpay/pending
- PATCH /netpay/investigation/{service_case_id}
- POST /netpay/shipment/{service_case_id}
- GET /netpay/devices
- GET /netpay/timeline/{service_case_id}

Alias de compatibilidad para algunos endpoints siguen disponibles en rutas previas bajo /netpay/service-cases/*.

## Seguridad

- Integracion actual: importacion manual, sin credenciales en Git.
- Correo tratado como `Confidential`.
- Sin automatizacion de Portal Socios NetPay.
- Sin envio de payloads de correo a proveedores externos de IA.
- Sin secretos, tokens o credenciales en repositorio.

## Limitaciones

- No hay conector Gmail activo en esta version.
- No hay automatizacion de Portal NetPay.
- No hay interfaz React NetPay en Sprint 7.1A.
- No incluye WhatsApp ni Google Drive.
- No incluye ventas, rentabilidad ni semaforo.
- CSV de inventario soportado; XLSX queda para siguiente paso.

## Pasos futuros

- Integrar Gmail read-only con permisos minimos.
- Integrar Portal NetPay bajo aprobacion y controles.
- Añadir capa de ventas.
- Añadir rentabilidad.
- Añadir semaforo operativo.
- Integrar WhatsApp.
- Integrar Google Drive.
