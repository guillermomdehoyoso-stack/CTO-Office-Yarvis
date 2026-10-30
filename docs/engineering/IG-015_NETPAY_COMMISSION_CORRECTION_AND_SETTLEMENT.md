# IG-015 — Core corregido y liquidación de comisiones

**PASS TÉCNICO LOCAL — GATES A–F CERRADOS; ACTIVACIÓN OPERATIVA NO AUTORIZADA**
Fecha: 2026-10-28. Autoridad: [Amendment 028](IMPLEMENTATION_ROADMAP_AMENDMENT_028.md).
Ratificación explícita del usuario: ejecución A–E en entorno local sintético,
con migración solo en PostgreSQL aislado y desechable. Preservar trabajo previo,
historia v1 y fronteras de identidad; sin importación real, activación, commit,
push ni despliegue. Los criterios siguientes fueron vinculantes para el cierre.

## Secuencia y criterios de salida

| Gate | Trabajo permitido después de ratificar | Evidencia de salida |
| --- | --- | --- |
| A | Revalidar árbol/HEAD, cambios ajenos, registro de contratos, perfiles y grafo Alembic | Diff atribuible; ningún cambio de identidad; revisión aditiva única |
| B | Core v2, componentes Decimal, AS separado, compatibilidad v1 | Pruebas de cálculo, procedencia, ausencias, encabezados y agregación |
| C | Liquidación, captura multientidad, validación e idempotencia | Controles sintéticos, aislamiento, replay/concurrencia y sin pérdida de movimientos |
| D | Conciliación y dashboard read-only | API/UI/browser muestran alcance, diferencias, pendientes y banco no confirmado |
| E | Cierre técnico local | Pruebas afectadas, migración reversible en PostgreSQL desechable, revisión y evidencia nueva |

No se ejecutan gates B-E antes de ratificación. No hay gate operativo implícito.
El PASS anterior IG-014 no cambia ni se reabre; su transición sigue bloqueada.

## Allowlist propuesta

- `apps/api/src/yarvis_api/models/netpay_operational_data.py` y su schema;
  `api/routes/netpay_data.py` para perfiles, aceptación y verificación de fuente.
- Nuevos `services/netpay_commission_settlement.py` y
  `services/netpay_commission_reconciliation.py` como helpers del owner Netpay.
- `services/historical_ingestion.py` solo para mapeo explícito de los componentes
  y preservación de evidencia; no promoción ni backfill.
- `services/netpay_commerce_attention.py`, su schema y ruta para proyección.
- `canonical_contracts.py` y catálogo documental solo en las entradas Netpay
  afectadas; preservar íntegro el trabajo local de Governance.
- Una migración aditiva según Amendment 028, exclusivamente nueva.
- `apps/web/src/api/netpay.ts`, `NetpayCommerceAttentionPortfolio.tsx`, su test
  y `apps/web/e2e/netpay-commerce-attention.spec.ts`; preservar cambios previos.
- Tests de Operational Data, D1, histórico, Portfolio, contratos y migración;
  nuevos tests focales de liquidación/conciliación y fixtures sintéticos.
- Evidencia nueva; actualizar estado/sprint únicamente al cerrar el paquete.

## Casos de aceptación preparados (pendientes de implementación)

Todos los importes de fixtures serán Decimal; no datos reales en fixtures.

| Caso | Entrada | Resultado exigido |
| --- | --- | --- |
| Fórmula | AP=10, AQ=5, AR=85, AS=700, volumen=1000 | Comisión=100, tasa=10%, beneficio=700; cambiar AS no altera comisión |
| Cero | AP=AQ=AR=0, volumen=1000 | Comisión=0 y tasa=0%; no ausencia |
| Negativo | AP=0, AQ=0, AR=-25, volumen=1000 | -25 y -2.50%; signo preservado |
| Ventas cero | Comisión=100, volumen=0 | Comisión sigue 100; porcentaje null, `volume_zero`, «No calculable» |
| Ausencias | Cada componente null por separado; volumen null | Comisión null si falta componente; causa específica, jamás fillna(0); volumen ausente produce tasa null |
| Beneficio ausente | AS null con componentes completos | Comisión y tasa válidas; beneficio null, sin derivarlo |
| Totales | (ventas=100, comisión=10) y (900,45) | Tasa=5.50%, no promedio 7.50%; cada Store cuenta una vez |
| Cobertura | Store con ventas 0 y comisión 20 | 20 visible en total monetario; excluido solo de población de tasa; ambas coberturas explícitas |
| Periodos | Mismo Store septiembre/octubre y versiones efectivas distintas | Conciliar solo periodo seleccionado; no sumar latest de meses distintos |
| Encabezados | Reordenar AP/AQ/AR por nombre | Igual resultado; nombre desconocido o duplicado normalizado bloquea perfil |
| Encabezados repetidos | Bloques con cabeceras en filas 7,152,161 | Excluir exactamente cabeceras y conservar filas físicas; cabecera alterada falla, no se descarta silenciosamente |
| Multimovimiento | Store X, comisión 10, bono 3, deductiva -2 | Tres movimientos, neto 11, procedencia individual |
| Multientidad | Asesor y Distribuidor con Store/concepto/importe iguales; Asociado 15 | Conservar los tres; total no deduplicado; facetas separadas |
| Igualdad real | Dos filas idénticas en mismo archivo | Dos movimientos; identidad por fila, no hash semántico |
| Sin Store | Cargo general -950, Store vacío | Neto del lote lo incluye; cola sin Store; no distribuir entre comercios |
| Sin correspondencia | Store no Master o no Core | Visible con causa y detalle bajo permiso; ninguna creación/match por nombre |
| Conceptos | Texto desconocido o reversión | Original intacto; desconocido pendiente, no compensación inferida con Core |
| Devengo/pago | Periodo septiembre y pago anunciado octubre | Devengo 2026-09; fecha 2026-10-15; banco no confirmado |
| Control | Cabecera 11, detalle 10 | Aceptación bloqueada por diferencia; no fabricar ajuste |
| Replay | Mismos bytes/Organization/perfil/clave | Mismo lote y movimientos, sin doble suma ni eventos duplicados |
| Conflicto/concurrencia | Misma clave con otros bytes; dos aceptaciones concurrentes | Conflicto en primero; una aceptación efectiva en segundo |
| Archivo corregido | Nuevos bytes para mismo periodo | Nuevo lote pendiente con predecesor/razón; sin last-write-wins ni dedup por importe |
| Precisión | 0.005 + 0.005 | Sumar antes de presentación HALF_UP; registrar precisión y no redondear cada operando |
| Legacy | V1 con AS=700 y sin componentes | Comisión null con causa; AS no se reetiqueta como comisión; historia preservada |
| Seguridad | Organization distinta, scope ausente, intento de PII | Denegación/concealment; sin nombres/correos en métricas/logs; permisos intactos |
| Banco | Neto fuente completo sin evidencia bancaria | `not_confirmed`; ni «pagado» ni fecha de depósito inferida |
| Migración | Upgrade/downgrade/re-upgrade en DB sintética | Preserva datos anteriores; downgrade con datos nuevos protegido contra pérdida |

Ejecutar tests backend afectados con PostgreSQL aislado, Vitest del Portfolio y
un recorrido Playwright list/detail/conciliación. Registrar comandos y resultados
reales al ejecutar; no trasladar los conteos históricos de IG-012/014 a este gate.

La inspección del 2026-10-28 ejecutó solamente el auditor offline de fuentes y
verificaciones documentales. El cierre técnico posterior del 2026-10-29 se
registra en
[`netpay-commission-ig015-conformance-20261029.txt`](evidence/netpay-commission-ig015-conformance-20261029.txt).
Ese cierre usa únicamente fixtures sintéticos y PostgreSQL aislado y desechable.
No valida los bytes del archivo real, no acredita depósito bancario y no
autoriza importación real, reprocesamiento histórico, despliegue ni producción.

## Gate F — validación de fuente real

**PASS — FUENTE REAL IDENTIFICADA, CONTROLES Y ACEPTACIÓN AISLADA VERIFICADOS (2026-10-29).**

El primer intento quedó `BLOCKED` porque el adjunto entonces autorizado no se
expuso mediante una referencia inequívoca. Después, el usuario sustituyó esa
restricción y autorizó expresamente la ruta literal de
`GUILLERMO MARIO DE HOYOS OLIVERA (3).xlsx`. La fuente accesible tiene SHA-256
`04ca3675a8075c119a4db503a71e9ddb3759df525dce66be534aea1d29eb7978`
y reproduce por auditoría XML independiente los 291 movimientos y controles
financieros esperados. Esa huella coincide con la evidencia offline registrada
el 2026-10-28.

El segundo estado fue `FAIL`: el parser rechazaba los nombres ZIP no canónicos
`xl\_rels\workbook.xml.rels` y `_rels\.rels`. La remediación local posteriormente
autorizada normaliza separadores sólo en memoria, conserva los bytes y la huella
de la fuente y mantiene límites y rechazos explícitos para rutas inseguras,
colisiones, relaciones externas y paquetes malformados.

Sobre los bytes finales del workspace, dos parseos fueron deterministas y
reprodujeron 291 movimientos, 25,668.64 positivos, -8,187.85 negativos y
17,480.79 netos, iguales a cabecera; Asesor 140, Distribuidor 147, Asociado 15 4
y seis movimientos sin Store. En PostgreSQL local aislado, staging y replay
produjeron un solo lote de 291 movimientos y dos aceptaciones concurrentes una
sola transición. La cobertura sintética conserva movimientos legítimos
repetidos. `BLOCKED` y `FAIL` quedan como antecedentes, con un único estado
vigente `PASS`. Evidencia:
[`netpay-commission-ig015-gate-f-source-validation-20261029.txt`](evidence/netpay-commission-ig015-gate-f-source-validation-20261029.txt).
