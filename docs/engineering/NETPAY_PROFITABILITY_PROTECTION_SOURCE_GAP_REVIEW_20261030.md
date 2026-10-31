# Revisión de fuentes y brechas — Protección de rentabilidad Netpay

**PROPOSED — DESIGN AND IMPLEMENTATION AUTHORIZATION DRAFT — NOT RATIFIED**

Fecha: 2026-10-30

Base inspeccionada: `5c5cb8c4a93a96754b2e8c273b315e2da68fc68a`

Propósito: separar hechos confirmados del repositorio de campos pendientes de
verificación. No autoriza lectura de nuevas fuentes reales ni implementación.

## 1. Evidencia confirmada

| Área | Confirmado en repositorio | Consecuencia |
| --- | --- | --- |
| Identidad comercial | `NetpayStoreReference` es tenant-scoped y Store ID activo es único por Organization | Store exacto puede componer fuentes; no crea terminal/MID/serie |
| Master/contacto | Client, Company y Branch contienen contactos y Portfolio tiene límites sensibles | listado minimizado; PII completa sólo bajo permiso vigente |
| Rentabilidad mensual | lote, fila, periodo, moneda, Store, Decimal, AP/AQ/AR, AS y versión semántica existen | usar “Reporte mensual de rentabilidad Netpay”; AP+AQ+AR y AS separado |
| Liquidación | lote/movimientos preservan entidad, Store opcional, concepto, signo, periodo, moneda y fila | posible medir cargos observados sin inferir causa ni banco |
| No Uso técnico | existe dataset `no_usage_campaign`, metadata pendiente, meses sin uso y estado de seguimiento | no demuestra el contrato del próximo archivo real ni terminal/serie |
| Cartera | lista/detalle read-only, reconciliación y permisos de Portfolio existen | puede componerse una vista futura sin transferir propiedad |
| Migraciones | grafo inspeccionado linealiza en `20261028_55` | 56 es sólo candidato sujeto a revalidación |
| Contratos runtime | Netpay llega a CMD-042, QRY-024 y EVT-030 | siguientes candidatos 043/025/031; catálogo resumido requiere reconciliación |

## 2. No confirmado

No se inspeccionó en esta tarea una muestra autorizada del Reporte mensual de No
Uso, Reporte Global de terminales, carta/cotización ni confirmación de
recepción/inventario. Por tanto permanecen `TO BE VERIFIED`:

- nombres exactos de hojas y encabezados;
- grano de fila y repetición de encabezados;
- presencia y semántica de Store, terminal ID, MID y número de serie;
- periodo, fecha de corte, última transacción y productor;
- importe, moneda y concepto de una penalización de No Uso;
- correspondencia entre conceptos de liquidación y No Uso;
- tasas, unidades, impuestos, vigencia, giro e incentivo en carta/cotización;
- fuente autoritativa de estado/recepción de equipo;
- evidencia que confirma que una penalización dejó de repetirse.

Los documentos preservados IG-013/Amendment 026 y sus evidencias no se usaron
como autoridad vigente. Sus archivos continúan fuera del alcance.

## 3. Matriz de aceptación de fuentes

| Control | Resultado exigido en Gate A/G |
| --- | --- |
| Identidad del archivo | nombre efectivo, ruta/recurso autorizado, tamaño y SHA-256 |
| Estructura | hojas, dimensiones, encabezados exactos y filas no transaccionales |
| Semántica | definición de cada campo suministrada o estado pendiente explícito |
| Temporalidad | recepción, generación, corte, devengo y vigencia separados |
| Precisión | lectura Decimal/token original; signo y escala preservados |
| Identidad | Store/terminal/MID/serie observados por separado; sin match por nombre |
| Trazabilidad | lote, archivo, hoja/fila, perfil y versión en cada observación |
| Determinismo | dos parseos de los mismos bytes producen el mismo resultado |
| Idempotencia | replay no duplica; filas legítimas repetidas se conservan |
| Seguridad | no se imprimen PII ni contenido sensible en logs/evidencia general |

## 4. Brechas de diseño que bloquean gates posteriores

- Gate C queda BLOCKED hasta confirmar corte/grano de No Uso y regla de
  penalización aplicada/probable.
- Gate D queda BLOCKED hasta verificar condiciones, unidades, vigencia y fuente
  de costo efectivo.
- Gate E puede diseñarse con fuentes sintéticas, pero una afirmación real exige
  suficientes periodos contiguos y versiones compatibles.
- Gate F requiere decidir si las capacidades existentes cubren las nuevas
  mutaciones; esta propuesta no amplía roles.
- Gate G exige autorización literal para cada fuente real y no acepta equivalencia
  por nombre de archivo.

## 5. Recomendación

La primera ratificación debe limitarse a Gates A y B: reconciliación de
contratos, inventario de fuentes, modelo de identidad y pruebas sintéticas. No
debe abrir cola de contacto, aceptar fuentes reales, calcular recuperación real
ni reservar definitivamente contratos/migración hasta resolver las brechas.
