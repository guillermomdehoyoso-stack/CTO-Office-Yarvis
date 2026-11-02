# IG-016A — revisión de perfiles de fuente y contratos

**RATIFIED FOR C1/C2 ONLY — C3/C4 REMAIN PROPOSED AND CLOSED**

Fecha: 2026-11-01

Base: `c43361a491db9a8c0d4f8b3d190dd2faef4d0a15`

Fuente de hechos agregados: [Gate G](evidence/netpay-profitability-protection-ig016-gate-g-20261031.txt)

## 1. Convenciones comunes de perfil

Cada perfil declara `profile_name`, `profile_version`, firma de posiciones y
encabezados, hojas, filas de encabezado, tipos, límites, grano y reglas de
clasificación. El parser futuro debe:

- leer bytes sin modificarlos y calcular SHA-256 antes de interpretar;
- rechazar macros, cifrado, links externos, fórmulas y ZIP inseguro;
- limitar tamaño, hojas, filas, columnas y longitud de celdas;
- preservar hoja/fila y original/normalizado para campos no PII aceptados;
- aplicar NFKC, trim y conversión integral controlada sin quitar ceros
  significativos;
- tratar nombres de archivo como metadato, nunca periodo o perfil;
- rechazar firma distinta como `incompatible_source_profile`;
- producir sólo preview efímero en C1.

Razones comunes: `placeholder`, `cell_error`, `blank`, `template_row`,
`missing_store`, `missing_equipment`, `missing_client`,
`missing_temporality`, `unsupported_value`, `ambiguous_identity`,
`contradictory_identity` e `incompatible_source_profile`.

El hash de Gate G identifica un lote de referencia, no autoriza todos los bytes
que compartan nombre o estructura.

## 2. Perfil `netpay_no_usage_oct26_v1`

| Propiedad | Propuesta |
| --- | --- |
| Lote Gate G | `2f93cb0589219642c129c764ce29328974400a1a942b068f7b09b466e1899d0c` |
| Hoja | sólo `Sheet1`, visible |
| Dimensión de referencia | `A1:O1001`; no se fija el número de filas para otros lotes |
| Encabezado | fila 1, 15 posiciones; J/K vacías se conservan en firma |
| Obligatorios | `#`, `Store ID`, `Store Name`, `Master Name`, `Distributor Name`, `Estatus`, `Meses No Uso`, `Alertas` |
| Opcionales | motivo, compromiso, renta, cancelación y comentarios; posiciones vacías explícitas |
| Grano | una fila de campaña observada por Store dentro del lote |
| Identidad | `Store ID` exacto; ningún campo de equipo |
| Temporalidad | ausente; nombre `Oct26` no se usa |

Tipos: `#` entero de plantilla; Store token string/integral; meses entero no
negativo o blank; estado/alerta texto controlado pero no reinterpretado; campos
de seguimiento texto/fecha sólo si el perfil posterior define semántica.

Clasificación:

- fila con sólo número y sin Store: `excluded/template_row`;
- Store blank: no crea registro de negocio;
- Store inválido: `invalid/unsupported_value`;
- Store válido sin Global: `pending/missing_equipment`;
- ningún campo crea periodo, terminal, MID, TID o penalización.

Preview mínimo: filas físicas, filas de negocio, template rows, Stores únicos,
duplicados, exactos contra cada lote Global, pendientes y campos de seguimiento
presentes. Referencia Gate G: 1,000 / 32 / 968 / 32.

## 3. Perfil `netpay_global_equipment_oct26_v1`

| Propiedad | Propuesta |
| --- | --- |
| Lote Gate G | `58bb41ec0d273122820822362953565e3aa82c092b75b5377c98c7c06f49c6d7` |
| Hoja | sólo `Sheet1`, visible |
| Dimensión de referencia | `A1:Q347` |
| Encabezado | agrupación fila 1; encabezado fila 2; A vacía |
| Obligatorios | `Serial TPV`, `Estatus de producto`, `Numero de comercio`, `Nombre del comercio`, `Numero de terminal`, `Folio`, `Producto`, `Fecha de creacion` |
| Opcionales | columnas declaradas Client/representante/RFC/razón/domicilio/teléfono; en lote de referencia están vacías |
| Grano | una observación de producto/asignación por fila |
| Identidad | Store observado=`Numero de comercio`; terminal y serie separados |
| Temporalidad | `Fecha de creacion` no es corte ni vigencia |

Normalización de Store/terminal/serie conserva original y token NFKC-trim. El
literal case-insensitive `NA` tras trim se clasifica placeholder en terminal y
serie. No se convierte `Numero de comercio` en MID.

Preview mínimo: 345 observaciones de referencia; 137 tokens normalizados; 209
observaciones `NA`; 136 equipos distinguibles; 327 Stores; 18 sin Store;
duplicados y relaciones multi-Store por identidad.

## 4. Perfil `netpay_ticket97580_equipment_client_oct26_v1`

| Propiedad | Propuesta |
| --- | --- |
| Lote Gate G | `b22849379cfa03a70edda41744ae0956a5667ccbb8e92b596fcf4e5a84f896da` |
| Hoja | sólo `Sheet1`, visible |
| Dimensión de referencia | `A1:Y348` |
| Encabezado | agrupación fila 1; encabezado multinivel filas 2–3; A vacía |
| Obligatorios base | los ocho campos del Global |
| Obligatorios de enlace | `Client ID`, `Company Id`, `Branch Id` como tokens opcionalmente cero/blank |
| Sensibles | representante, correo, teléfonos, RFC, razón social y campos de domicilio |
| Grano | misma observación de producto/asignación, enriquecida; lote independiente |
| Temporalidad | no confirmada; enriquecimiento no demuestra vigencia |

Los subencabezados de domicilio `ESTADO`, `CIUDAD`, `CP`, `COLONIA`, `CALLE`,
`NO EXTERIOR`, `NO INTERIOR` son parte de la firma. `#N/A` es `cell_error`; no
se normaliza como texto de negocio. Error de domicilio no invalida Store,
terminal, serie o Client ID válidos.

En este perfil, y solo en `Client ID`, cero numerico o la cadena exacta `0` despues de retirar espacios exteriores se clasifica `missing_client`; no crea identidad `"0"`. `00`, `0.0`, negativos y textos que contienen cero no comparten la regla. Store, terminal y serie conservan su normalizacion propia.

En C1 se permiten conteos/presencia y correspondencia por IDs. No se emite PII.
En aceptación futura, Client/Company/Branch se resuelven a referencias Master;
PII original no se duplica en filas operativas. Si se exige conservar bytes o
valores sensibles como evidencia, requiere retención restringida separada.

Preview mínimo: 345 observaciones; 136 equipos distinguibles; 118 con cliente;
18 sin cliente y Store; 209 observaciones `NA`; 18 `#N/A` en ESTADO; conflictos
contra Global y disponibilidad de email/teléfono por conteo.

## 5. Compatibilidad entre perfiles

- No Uso sólo puede enlazar por Store exacto.
- Global y Ticket comparan base por Store + terminal + serie + folio, conservando
  cada fuente/fila.
- Ticket no supersede Global. Una diferencia produce `contradictory_identity` o
  `unsupported_value`, no elección automática.
- Los 20 matches de Gate G son `pending/missing_temporality` aunque Store,
  terminal, serie y cliente coincidan.
- Los 12 Store-only quedan `pending/missing_equipment`.
- Los 18 equipment-only quedan `pending/missing_store` y `missing_client`.
- Un archivo con columnas, orden, merged headers, hoja o tipo incompatible no se
  adapta heurísticamente; requiere perfil/version nueva y revisión.

## 6. Preview contract

### IC-NETPAY-QRY-025 `PreviewNoUsageRecoverySources`

- Actor: `netpay_operations_operator`; `netpay.inbox.manage`.
- Input: Organization del envelope, perfil solicitado, uno o más archivos
  allowlisted, hashes esperados y opciones de preview sin PII.
- Output: token efímero, firmas, hashes, métricas, clasificación agregada,
  excepciones seguras y matriz de correspondencia.
- Idempotencia: mismos bytes + perfiles + opciones producen mismo token/salida;
  no existe receipt persistido en C1.
- Errores: tamaño, ZIP, macro, fórmula, hoja, firma, tipo, hash y límite; códigos
  seguros sin valores de celda.
- PII: sólo presencia/conteos; nunca valores.
- Evento: ninguno.
- Consumidor: checkpoint humano local.
- Gate: C1.

## 7. Acceptance and readback contracts

### IC-NETPAY-CMD-043 `AcceptNoUsageRecoverySource`

- Actor: operations operator con `netpay.inbox.manage`.
- Input: bytes/hash, perfil/version, preview token, decisión de checkpoint,
  idempotency key, expected Store-state hash y razón; sin PII en key.
- Output: batch ID, estado, conteos, temporalidad, accepted/pending/excluded y
  readback reference.
- Idempotencia: receipt por Organization+command+key+fingerprint; concurrencia
  acepta un lote.
- Errores: preview mismatch/expired, hash/profile conflict, Store-state conflict,
  incompatible format, unauthorized, idempotency conflict.
- PII: no valores en respuesta general.
- Evento: ninguno; C2 usa historial interno append-only porque no existe consumidor real para EVT-031.
- Consumidor: proyección de source review y futura inicialización explícita de
  casos; auditoría.
- Gate: C2.

### IC-NETPAY-QRY-026 `RetrieveNoUsageSourceReview`

- Actor: inbox read; excepciones requieren reconciliation read.
- Input: batch ID y filtros seguros.
- Output: lote, perfil, métricas, filas clasificadas minimizadas, links y
  procedencia; detalle sensible omitido.
- Idempotencia: query read-only.
- Errores: not found/concealed, unauthorized, provenance invalid.
- PII: ninguna en listado; referencia canónica opaca solamente.
- Evento: ninguno.
- Consumidor: checkpoint/readback humano.
- Gate: C2.

## 8. Case contracts

### IC-NETPAY-CMD-044 `OpenOrUpdateNoUsageRecoveryCase`

- Actor: operations operator con inbox manage.
- Input: link evidenciado, motivo, responsable, acción, compromiso,
  expected_version e idempotency key.
- Output: case ID, state/version y safe summary.
- Idempotencia: receipt y unicidad de caso activo por causa+link+periodo
  verificable; no se usa PII.
- Errores: temporalidad pendiente para estado contactable, duplicate case,
  invalid transition/version, foreign tenant, unauthorized.
- PII: referencias canónicas; `contact_available` únicamente.
- Evento: EVT-032 `NoUsageRecoveryCaseChanged`.
- Consumidor: cola minimizada y auditoría.
- Gate: C3.

### IC-NETPAY-CMD-045 `RecordNoUsageRecoveryAction`

- Actor: operations operator; inbox manage; sensible read si la acción usa
  contacto.
- Input: case ID/version, tipo, outcome seguro, próxima acción/fecha, nota segura,
  evidencia e idempotency key.
- Output: nueva versión/estado e historial seguro.
- Idempotencia: receipt; expected-version evita last-write-wins.
- Errores: invalid state, missing authority/evidence, version/idempotency conflict.
- PII: canal tipificado, no dirección/correo/teléfono ni nota en evento.
- Evento: EVT-032 con `change_kind`, IDs y estado.
- Consumidor: cola y auditoría.
- Gate: C3.

### IC-NETPAY-QRY-027 `ListOrRetrieveNoUsageRecoveryCases`

- Actor: portfolio read; sensitive read para contacto completo; reconciliation
  read para identidad pendiente.
- Input: filtros, sort/pagination o case ID.
- Output: lista minimizada o detalle autorizado/historial.
- Idempotencia: query read-only.
- Errores: concealed/not found/unauthorized.
- PII: omitida por defecto; acceso sensible auditado.
- Evento: ninguno; acceso sensible produce registro de auditoría interno.
- Consumidor: operador humano.
- Gate: C3.

## 9. Outcome contract

### IC-NETPAY-CMD-046 `VerifyNoUsageRecoveryOutcome`

- Actor: operations operator con inbox manage.
- Input: case/version, tipo de outcome, referencias de evidencia, periodo/ventana,
  componentes financieros, certeza e idempotency key.
- Output: outcome ID, estado, componentes incluidos/excluidos y nueva versión.
- Idempotencia: receipt y fingerprint; snapshot append-only/superseding.
- Errores: evidence missing, incomparable period/concept, overlapping component,
  invalid certainty/state/version, idempotency conflict.
- PII: ninguna.
- Evento: EVT-033 `NoUsageRecoveryOutcomeVerified`.
- Consumidor: proyección de métricas Netpay y auditoría; no ledger/caja.
- Gate: C4.

## 10. Event payloads

| Evento | Payload seguro | Prohibido |
| --- | --- | --- |
| EVT-031 | org, batch, profile/version, hash reference, counts, actor, correlation | filename local, PII, filas |
| EVT-032 | org, case, link, prior/new state, version, change kind, actor, correlation | contacto, Client ID externo, nota |
| EVT-033 | org, case, outcome, certainty, period, component categories, actor, correlation | PII, banco inferido, evidencia textual |

Si no existe consumidor real o necesidad de auditoría demostrada al ratificar,
el evento correspondiente no se registra.

## 11. Persistencia candidata y migración 57

La revisión `20261031_57` implementa exclusivamente el diseño lógico C2:

- source batch: Organization, profile/version, source hash, safe filename,
  sheet, temporal metadata, status, counts, actor y timestamps;
- classified row: batch, sheet/row, classification/reasons, original/normalized
  de identificadores no PII, fingerprints, Store/equipment link y procedencia;
- recovery case: refs canónicas, motivo, estado, responsable, próxima acción,
  compromiso y aggregate version;
- case history: append-only prior/new state, safe reason, actor, evidence refs;
- outcome evidence/snapshot: tipo, periodo, certeza y componentes disjuntos;
- receipts: Organization, command, idempotency key, fingerprint y resultado.

Se reutilizan `netpay_equipment_*` de revisión 56 y Master. No se duplican
contactos. Constraints son tenant-scoped y downgrade revierte en orden inverso.
C3 y C4 requieren revisiones y ratificaciones separadas; no están incluidas en 57.

## 12. Retención y auditoría

- SHA-256, perfil, hoja/fila, clasificación y decisiones se conservan según
  política futura de Operational Data.
- C1 no retiene bytes ni preview tras la respuesta.
- C2 debe declarar si descarta bytes tras aceptación o usa evidencia restringida;
  no queda decidido por este borrador.
- Acceso sensible registra sujeto, actor, propósito y correlación sin valor PII.
- Eventos y logs usan referencias opacas y códigos seguros.

## 13. Riesgos y decisiones abiertas

- Sin corte/vigencia no existe asignación actual confirmada.
- La relación Client del Ticket puede ser histórica o administrativa.
- `netpay.inbox.manage` es amplio; C3 debe probar la conjunción con sensitive
  read o solicitar Governance, sin añadir rol por conveniencia.
- El mapa de deductivas No Uso y la ventana de ausencia aún no existen.
- La recepción/inventario canónica del equipo está por definir.
- La retención de bytes/PII fuente requiere decisión explícita.
