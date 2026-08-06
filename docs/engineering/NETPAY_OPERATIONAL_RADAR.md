# Radar Operativo Netpay

## Uso local

El RADAR es un vertical manual y síncrono para seguimiento de solicitudes Netpay.

```powershell
docker compose exec api alembic upgrade head
docker compose exec api python -m yarvis_api.radar_seed
```

Abrir `http://127.0.0.1:5173/radar-netpay`. La pantalla usa el workspace local
`netpay-demo`; no hay integración de correo, mensajería, OCR ni ejecución diferida.
El seed es explícito, idempotente y no se invoca al iniciar la aplicación.

## Diseño y reglas

`radar_merchants`, `radar_requests`, `radar_checklist_items` y
`radar_activities` son registros PostgreSQL aislados por `workspace_id`. Cada
solicitud se clasifica manualmente y puede crear su comercio en una operación
atómica. Las altas TPV crean seis requisitos; e-commerce reutiliza los seis y
añade la evidencia de control de dominio. Los documentos recibidos guardan actor
y fecha. La bitácora es append-only también en PostgreSQL.

El indicador de comercio se deriva exclusivamente de solicitudes abiertas: ON
cuando existe al menos una y OFF cuando no existe ninguna. El cierre exige no
tener siguiente acción ni requisitos pendientes, o una justificación explícita.
Reabrir conserva el historial. El tablero ordena vencidos, prioridad, fecha
objetivo, antigüedad y nombre de modo determinista.

## Recorrido demostrado

El seed dejó cuatro comercios persistidos: Café Horizonte (TPV cerrado),
Gasolinera La Providencia (alta e-commerce con siete faltantes), Farmacia del
Centro (reposición vencida) y Mercado Alameda (una solicitud cerrada y otra
abierta). Tras reiniciar sólo la API, `GET /radar/dashboard` devolvió los mismos
cuatro comercios: 3 pendientes, 1 vencido, 2 TPV y 2 e-commerce.

La política local del navegador bloqueó la captura automatizada de `127.0.0.1`.
La página quedó compilada y disponible en la URL indicada. La validación HTTP
focalizada cubre registro, plantillas, ON/OFF, cierre/reapertura, justificación,
actor de documento, inmutabilidad, aislamiento, idempotencia, filtros y orden.

## Aceptación humana

Guillermo aceptó el recorrido visible en `http://127.0.0.1:5173/radar-netpay`:
editó y resolvió la siguiente acción, completó el checklist, cerró la solicitud
y observó el cambio del comercio de PENDIENTE ON a PENDIENTE OFF. La recarga
posterior conservó el cierre y la bitácora, confirmando la persistencia.

En desarrollo local, después de cambios de frontend se debe reiniciar Vite para
evitar una transformación anterior del bind mount de Windows:

```powershell
docker compose restart web
```

Después, abrir o recargar de forma dura `http://127.0.0.1:5173/radar-netpay`.

## Límites

No se inició F-011, F-016 ni F-017. No se modificó F-012/F-013 ni el catálogo
fundacional. No hay workers, colas, brokers, schedulers, microservicios, Gmail,
WhatsApp, dispatch posterior ni abstracciones horizontales.
