# Revisión de fuentes y brechas — Protección de rentabilidad Netpay

**PROPOSED — DESIGN AND IMPLEMENTATION AUTHORIZATION DRAFT — NOT RATIFIED**

Fecha: 2026-10-30

Base inspeccionada: `5c5cb8c4a93a96754b2e8c273b315e2da68fc68a`

Propósito: separar hechos confirmados del repositorio de campos pendientes de
verificación. No autoriza lectura de nuevas fuentes reales ni implementación.

## Actualización ejecutada de Gate G — 2026-10-31

La autoridad literal posterior permitió inspeccionar tres fuentes reales como
lotes independientes. El resultado vigente es **PASS CON BRECHAS** y no cambia
la naturaleza propuesta de este documento ni abre importación:

| Fuente | SHA-256 | Estructura y grano observado |
| --- | --- | --- |
| Comercios No Uso Oct26 | `2f93cb0589219642c129c764ce29328974400a1a942b068f7b09b466e1899d0c` | `Sheet1` `A1:O1001`; 32 filas de negocio Store/campaña y 968 filas de plantilla sin Store |
| Reporte Global Netpay GD Oct26 | `58bb41ec0d273122820822362953565e3aa82c092b75b5377c98c7c06f49c6d7` | `Sheet1` `A1:Q347`; encabezado fila 2 y 345 observaciones de producto/asignación |
| Ticket 97580 Reporte Global Netpay GD Oct26 | `b22849379cfa03a70edda41744ae0956a5667ccbb8e92b596fcf4e5a84f896da` | `Sheet1` `A1:Y348`; encabezado multinivel filas 2–3 y 345 observaciones enriquecidas |

Los Globales conservan 136 equipos distinguibles y 209 filas con un token
placeholder repetido en serie/terminal. Sus ocho campos base de equipo coinciden
sin altas, bajas, modificaciones ni contradicciones. Ticket 97580 agrega Client
ID para 118 equipos (86.76%; +86.76 puntos porcentuales frente al Global sin
clientes) y PII de cliente/contacto para las relaciones disponibles. Hay 26
clientes con más de un equipo; ninguna terminal distinguible se asocia a varios
clientes o Stores y ningún Store aparece con varias terminales en este corte.

No Uso no trae terminal, MID, serie, última actividad, fecha de corte ni periodo
interno confirmado. La correspondencia exacta por Store cubre 20/32 filas
(62.50%); las 12 restantes quedan sin correspondencia. Las 20 relaciones
coincidentes llegan a equipo, cliente y presencia de contacto en Ticket 97580.
No se usaron nombres, teléfonos, correos ni similitud textual como identidad.
Cada uno de los 20 Stores enlaza a un equipo; esos equipos llegan a 15 clientes,
por lo que existe una relación muchos Stores a un cliente en cuatro clientes
compartidos. “Contacto disponible” significa email o teléfono no vacío, no cero
y sin error; los 20 tienen ambos tipos. Los 18 equipos sin cliente carecen también
de Store y son distintos de los 12 Stores de No Uso que no aparecen en Global.

Persisten estas brechas antes de IG-016A operativa: `Oct26` es sólo etiqueta de
nombre; no existe MID explícito; la autoridad temporal y la vigencia siguen
ausentes; el placeholder requiere regla de perfil; Ticket contiene 18 errores
de celda en `ESTADO`; y los campos sensibles requieren la consulta sensible y
auditoría existentes. Los tres archivos deben conservarse como evidencia de sus
propias relaciones; Ticket evidencia cliente/contacto y ambos Globales evidencian
por separado la relación base coincidente. La preparación documental/técnica de
IG-016A puede avanzar con estas brechas explícitas, pero Gate C, aceptación real,
contacto y automatización permanecen cerrados.

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
