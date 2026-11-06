# IG-016A C4 — Resultados verificados y efectos financieros

**RATIFIED — C4 LOCAL SYNTHETIC IMPLEMENTATION AND VALIDATION ONLY**

Fecha: 2026-11-05

Roadmap propuesto:
[Amendment 032](IMPLEMENTATION_ROADMAP_AMENDMENT_032.md)

Base: `70c6f9397c0ec772ec19c3f5d84f7a61c4024a4c`

Dependencias: C1, C2 y C3 publicados; migración `20261102_58`; C4 abierto sólo
para implementación y validación local sintética.

Ratificado el 2026-11-06 sobre los borradores SHA-256
`B5EDF8C6710DA432396986EC5B426F3840756C936947B90117548F80998A60D8`
y `97C9BDC4EE57C3CCBEBE0273D67BC1EC2579DD1C01DF4DF71CFD40EF42F1FF29`.
La autoridad se limita a implementación local sintética, migración 59 y
CMD-049/050 + QRY-030; no abre ninguna exclusión de §16.

## 1. Objetivo y límite semántico

C4 separa tres hechos que nunca son intercambiables:

1. **Compromiso humano:** llamada, contacto, promesa, solicitud de devolución,
   responsable, plan o fecha. Vive en C3 y no prueba un resultado.
2. **Resultado operativo:** actividad posterior o recepción física verificada
   mediante evidencia autorizada, temporal y vinculada a la identidad correcta.
3. **Resultado financiero:** cargo, crédito, ausencia comparable o cálculo
   reproducible posterior, con procedencia, periodo, componentes y certeza.

Una llamada, promesa, solicitud, guía de envío o cambio de estado no prueba
reactivación, devolución, penalización evitada ni dinero recuperado. Un resultado
operativo tampoco prueba por sí solo efecto financiero o depósito bancario.

## 2. Modelo propuesto

### 2.1 Evidencia de outcome

Cada evidencia contiene Organization, caso y versión, tipo, perfil/version,
fuente autorizada, lote/hash o referencia opaca, coordenada o identificador de
registro, identidad observada, `occurred_at`, `observed_at`, periodo/corte,
moneda/unidad cuando aplique, actor, correlación y transaction time.

La evidencia original es inmutable. Una corrección crea una revisión que
supersede la anterior, conserva la cadena y obliga a recalcular evaluaciones
dependientes. No se almacenan bytes, PII, contacto ni texto libre.

### 2.2 Evaluación operativa

Estados candidatos:

- `pending_evidence`;
- `supported_store_level`;
- `reactivation_verified`;
- `return_in_transit`;
- `equipment_return_verified`;
- `contradictory`;
- `superseded`.

Una evaluación referencia exactamente la evidencia incluida/excluida, regla y
versión, instante de evaluación, certeza y brechas. No reescribe el historial C3.

### 2.3 Evaluación financiera

Categorías candidatas:

- `applied_penalty_observed`;
- `credit_observed`;
- `penalty_non_recurrence_supported`;
- `avoided_penalty_projected`;
- `recovered_amount_supported`;
- `recovered_amount_confirmed`;
- `financial_effect_not_calculable`.

Cada snapshot conserva entradas, fórmula, precisión Decimal, moneda, periodo,
mapa comparable/version, componentes incluidos/excluidos, certeza y razón de no
cálculo. No representa ledger ni caja. `bank_deposit_confirmed` queda fuera de
C4 salvo una autoridad y fuente bancaria posteriores y separadas.

### 2.4 Perfiles cerrados exclusivamente sintéticos

| Perfil | Autoridad sintética | Campos temporales obligatorios | Resultado permitido |
| --- | --- | --- | --- |
| `synthetic_c4_activity_v1` | fixture firmado por el harness local C4; nunca un lote C1/C2 real | `decision_at`, `occurred_at`, `observed_at`, `valid_from`, `valid_to`; todos con zona | `supported_store_level` o `reactivation_verified` |
| `synthetic_c4_return_inventory_v1` | fixture de recepción/inventario local; ubicación y estado de catálogo | `request_at`, `received_at`, `observed_at`, vigencia de identidad; todos con zona | `return_in_transit` o `equipment_return_verified` |
| `synthetic_c4_financial_effect_v1` | fixture de movimientos y completitud de periodo local | periodo devengado, `period_closed_at`, `observed_at`, ventana comparable | categorías financieras de §2.3 |

Los perfiles aceptan únicamente `source_authority = synthetic_fixture`,
Organization y referencias generadas por la suite, catálogos v1 exactos y
`environment = isolated_local`. Rechazan rutas, nombres de archivo, hashes,
batches, links, Stores, terminales, series o movimientos de las fuentes reales,
así como perfiles desconocidos, aliases o campos libres. Los permisos se toman
del `IdentityAuthorityEnvelope` del servidor; el fixture no declara rol ni
capability.

`valid_from <= occurred_at < valid_to`; `decision_at < occurred_at <= observed_at`
para actividad, y `request_at < received_at <= observed_at` para devolución. El
periodo financiero debe estar cerrado antes de `observed_at`. Intervalos vacíos,
invertidos, abiertos cuando el perfil exige cierre, timestamps sin zona o hechos
futuros producen errores deterministas. Los perfiles y autoridades de fuentes
reales siguen pendientes y sólo pueden decidirse para un piloto posterior.

## 3. Reactivación verificada

`reactivation_verified` requiere todo lo siguiente:

- decisión C3 previa de reactivación y versión esperada;
- evidencia aceptada de actividad posterior a la decisión;
- `occurred_at` dentro de la vigencia de la identidad Store–equipo aplicable;
- Store exacto y, para un caso de equipo, terminal o serie exacta;
- fuente/perfil autorizado que demuestre actividad, no sólo alta o existencia;
- ausencia de contradicción vigente o evidencia supersedida;
- actor, regla/version y procedencia completa.

Una transacción sólo vinculada al Store puede producir
`supported_store_level`; no verifica una terminal concreta. Volumen cero,
registro Master, fecha de creación, contacto, promesa o cambio manual de estado
no verifican reactivación. Evidencia posterior contradictoria deja el outcome
abierto o supersede la evaluación; no borra la anterior.

## 4. Devolución de equipo verificada

`equipment_return_verified` requiere:

- decisión C3 previa de devolución;
- terminal o serie exacta vinculada al caso;
- recepción o alta en inventario emitida por una fuente autorizada;
- evento posterior a la solicitud y dentro de una ventana válida;
- ubicación/estado receptor tipificado, referencia de registro y procedencia;
- ausencia de recepción anulada, identidad contradictoria o supersesión vigente.

Una guía, recolección solicitada, promesa, fotografía no gobernada, entrega al
transportista o estado escrito por el operador puede producir seguimiento o
`return_in_transit`, pero no recuperación verificada. Si sólo existe Store, el
equipo permanece sin verificar.

## 5. Efectos financieros demostrables

### 5.1 Penalización aplicada

Requiere movimiento firmado aceptado, moneda y periodo, identidad compatible y
concepto clasificado por un mapa versionado. Movimientos sin Store o conceptos
sin equivalencia permanecen visibles y no se asignan. El mismo movimiento no se
cuenta en más de un componente.

### 5.2 No recurrencia y penalización evitada

La ausencia sólo es evaluable si la fuente del periodo es completa, el concepto
es comparable, la identidad y moneda son compatibles y transcurrió la ventana
aprobada. La ausencia produce como máximo
`penalty_non_recurrence_supported`. `avoided_penalty_projected` requiere además
una regla aprobada para el importe esperado. No se presenta como ahorro
realizado. Confirmación del emisor sería otra evidencia explícita.

### 5.3 Importe recuperado

`recovered_amount_supported` exige un crédito, reversión o mejora posterior
atribuible mediante regla aprobada y componentes disjuntos. Sólo puede ser
`recovered_amount_confirmed` con evidencia financiera certificada que identifique
el importe y su relación con el caso. El neto reportado para pago, una mejora de
rentabilidad o un resultado operativo no demuestran depósito bancario.

### 5.4 Reglas de cálculo

- usar Decimal y moneda explícita; no mezclar monedas;
- periodos ausentes no son cero;
- componentes ausentes permanecen ausentes;
- conceptos no comparables quedan fuera con razón visible;
- una cifra participa una vez;
- certeza agregada es la menor de sus componentes;
- una supersesión recalcula desde las referencias vigentes y conserva snapshots
  anteriores como históricos;
- si falta base, mapa, ventana o periodo comparable, el resultado es
  `financial_effect_not_calculable`.

La escala cerrada de certeza es `projected < supported < confirmed`; nunca se
eleva por agregación y la certeza de un total es la menor de sus componentes.
`confirmed` significa evidencia financiera certificada dentro del perfil, no
depósito bancario. Los cálculos usan Decimal exacto, escala interna mínima de
seis decimales y `ROUND_HALF_EVEN` a dos decimales MXN sólo al materializar el
snapshot monetario. No se redondean entradas antes de sumar ni se usa float.

Fórmulas sintéticas v1:

- `applied_penalty_observed = abs(sum(min(amount, 0)))` para movimientos
  firmados incluidos por el mapa comparable de penalización;
- `credit_observed = sum(max(amount, 0))` sólo para créditos/reversiones
  comparables y atribuidos al caso;
- `penalty_non_recurrence_supported = max(0,
  comparable_baseline_penalty - observed_comparable_penalty)` únicamente con
  periodo completo y ventana satisfecha;
- `avoided_penalty_projected` usa la misma diferencia, pero permanece
  `projected` cuando la base esperada procede de regla y no de confirmación del
  emisor;
- `recovered_amount_supported = min(credit_observed,
  attributable_applied_penalty)`; cualquier excedente queda excluido con razón;
- `protected_profitability = recovered_amount_supported +
  avoided_penalty_projected`, sólo si ambos conjuntos de evidencia son
  disjuntos; no es caja confirmada.

La atribución exige Organization, caso, identidad compatible, familia de
concepto versionada, moneda y periodo posterior a la decisión. Cada fingerprint
de movimiento pertenece como máximo a un componente vigente. Un constraint de
atribución y la evaluación de solapamiento rechazan reutilización directa o
transitiva con `overlapping_financial_component`. Un crédito que revierte una
penalización no puede contarse también como mejora general de rentabilidad.

Cuando los componentes Core sean aplicables, la comisión del distribuidor sigue
siendo `AP + AQ + AR`, sólo si los tres están presentes; AS sigue siendo el
beneficio total combinado del distribuidor y Netpay. AS nunca sustituye la
comisión ni se suma otra vez a AP+AQ+AR. Componentes ausentes no se convierten en
cero y ventas cero mantienen la razón de comisión como `No calculable`.

## 6. Temporalidad y procedencia

Se distinguen:

- valid time de identidad y condición;
- `occurred_at` del hecho operativo o financiero;
- periodo devengado/corte de la fuente;
- `observed_at` de ingestión o revisión;
- transaction time de persistencia y supersesión.

Para fixtures sintéticos, `valid_from <= occurred_at < valid_to` cuando existe
`valid_to`; la evidencia debe ocurrir después de la decisión que pretende
verificar. Intervalos vacíos/invertidos, timestamps sin zona, periodos no
contiguos exigidos por la regla, hechos futuros o fuentes incompletas se
rechazan. El nombre del archivo nunca establece periodo o vigencia.

Procedencia mínima: perfil/version, hash o referencia opaca, hoja/fila o record
ID, productor, periodo/corte, actor de aceptación y cadena de supersesión. C4 no
acepta referencias genéricas ni evidencia textual libre.

## 7. Transiciones y cierre

C4 especializa estados C3 sin reescribirlos:

- `reactivation_agreed` o `monitoring` → `reactivation_verified` sólo con §3;
- `return_requested` o `monitoring` → `equipment_return_verified` sólo con §4;
- un outcome verificado → `monitoring` si falta ventana financiera;
- outcome operativo + evaluación financiera suficiente → cierre;
- evidencia contradictoria → `monitoring` o `escalated`;
- ausencia material → cierre con brecha explícita, nunca cierre exitoso implícito.

CMD-050 aplica esta matriz cerrada:

| `closure_kind` | Precondición de caso | Outcome vigente | Snapshot vigente | Brecha/razón | Respuesta | Error determinista si falta |
| --- | --- | --- | --- | --- | --- | --- |
| `verified_with_financial_effect` | `reactivation_verified` o `equipment_return_verified`; versión esperada | obligatorio, no contradictorio ni supersedido | obligatorio; `supported` o `confirmed`, moneda/periodo/regla completos y sin solapamiento | no permitida | `closed`, outcome/snapshot IDs y certezas | `operational_outcome_required`, `financial_snapshot_required`, `financial_component_overlap` o `stale_version` |
| `verified_financial_pending` | outcome operativo verificado; ventana financiera aún no cerrada o fuente sintética completa aún no disponible | obligatorio y vigente | opcional; si existe debe ser `financial_effect_not_calculable` | obligatoria: `financial_window_pending` o `financial_source_incomplete` | `closed`, outcome ID y brecha; ningún importe | `operational_outcome_required`, `pending_reason_required`, `unexpected_financial_amount` o `stale_version` |
| `closed_with_evidence_gap` | caso no terminal o `monitoring`/`escalated`; decisión humana de cierre | opcional; sólo `pending_evidence`, `supported_store_level` o `contradictory` | opcional; sólo no calculable y sin importe | obligatoria: catálogo de brechas | `closed`, brechas y referencias minimizadas; sin éxito declarado | `evidence_gap_required`, `verified_outcome_conflict`, `unexpected_financial_amount` o `stale_version` |
| `not_recoverable` | estado C3 `unrecoverable` o transición válida a él con razón de catálogo | opcional; no puede ser verificado exitoso | opcional; sólo pérdida/cargo observado o no calculable, nunca recuperación | obligatoria: razón `not_recoverable` | terminal, razón y evidencia segura | `not_recoverable_reason_required`, `successful_outcome_conflict`, `recovery_amount_forbidden` o `stale_version` |

Errores se evalúan en orden: autoridad/tenant oculto, idempotencia, versión,
estado, outcome, snapshot, solapamiento y brecha. El mismo request produce el
mismo código y body seguro. Ningún fallo crea historial, outcome, snapshot o
mutación parcial; sólo el receipt de conflicto autorizado por §8 puede quedar.

Sólo `verified_with_financial_effect` admite un efecto soportado/confirmado;
ningún cierre confirma banco. Un caso terminal no se reabre in-place: un nuevo
caso lo supersede y referencia el anterior.

### 7.1 Evidencia supersedida después del cierre

El cierre conserva para siempre los IDs y versiones que evaluó. Si CMD-049
agrega una corrección con `supersedes_evidence_id`, la evidencia anterior, el
snapshot y el cierre no cambian. La selección vigente se deriva de la hoja única
sin sucesor de cada raíz. QRY-030 marca la evaluación histórica como
`assessment_stale` cuando alguna dependencia ya no es vigente y devuelve por
separado la revisión vigente; nunca reescribe el resultado histórico.

Una corrección posterior al cierre requiere los mismos permisos de CMD-049,
`correction_reason` de catálogo, expected version de la raíz y referencia
explícita a la revisión reemplazada. Si la corrección cambia el significado del
cierre, un actor autorizado puede usar el CMD-045 vigente para crear un caso
sucesor con `supersedes_case_id`; no puede reabrir ni editar el caso terminal.
Dos correcciones concurrentes de la misma hoja producen un ganador y
`supersession_conflict` para el perdedor.

## 8. Idempotencia y concurrencia

Se reutiliza C3:

- Organization + command + idempotency key + fingerprint;
- mismo key/fingerprint: mismo status y body;
- mismo key con otro fingerprint: `idempotency_conflict` sin mutación;
- toda mutación exige `expected_case_version`;
- versiones concurrentes: un ganador y `stale_version` determinista para el
  perdedor, con receipt seguro y sin outcome/snapshot parcial;
- la misma evidencia lógica sólo puede tener una revisión vigente; carreras
  producen un ganador y `outcome_already_recorded`;
- cierre concurrente produce un ganador; replay conserva el cierre original;
- evidencia, evaluaciones y snapshots son append-only; UPDATE/DELETE se
  rechazan en base de datos;
- caso, historial, outcome, snapshot y receipt se confirman o revierten juntos.

Cada familia de revisiones forma un grafo lineal: raíz inmutable, cero o un
sucesor directo por revisión y una sola hoja vigente. `supersedes_id` es unique;
el servicio selecciona la hoja mediante ausencia de sucesor dentro de la misma
Organization y bloquea esa hoja durante la escritura. No existe `is_current`,
UPDATE de estado histórico ni borrado lógico mutable. Una bifurcación se rechaza
como `supersession_conflict`; ciclo, raíz ajena o salto de Organization se
rechazan como `invalid_supersession_chain`.

El receipt de éxito se confirma en la misma transacción que caso, historial,
evidencia, evaluación y snapshot. Para `idempotency_conflict`, `stale_version`,
`outcome_already_recorded`, `supersession_conflict` y conflicto de cierre, se
revierte primero cualquier savepoint de negocio y se persiste únicamente un
receipt seguro determinista en la transacción exterior. El receipt contiene
command ID, key, fingerprint, código, IDs/versión minimizados y body seguro; no
contiene payload, importe no autorizado ni PII. Una prueba de fallo inyectado
entre rollback y receipt debe dejar cero mutaciones de negocio y, según el punto
de fallo, cero receipt o exactamente un receipt completo, nunca uno parcial.

## 9. Autoridad, privacidad y retención

CMD-049/050 requieren permisos validados por servidor: `netpay.inbox.manage` y
`netpay.portfolio.reconciliation.read`. QRY-030 exige
`netpay.portfolio.read`; referencias detalladas exigen además reconciliation.
La matriz vigente describe a `netpay_operations_operator` como poseedor de la
conjunción, pero el request no declara rol ni permisos.

Todos los recursos se aíslan por Organization; recursos extranjeros se ocultan.
Respuestas, receipts, logs y errores excluyen contacto, PII, valores fuente no
minimizados y texto libre. Retención candidata: outcome, evaluación, snapshot,
receipt y auditoría por 24 meses desde cierre/supersesión. No se implementa
purga en C4; una política posterior debe conservar tombstone y trazabilidad.

## 10. Contratos candidatos

| ID | Input mínimo | Output mínimo | Errores seguros |
| --- | --- | --- | --- |
| CMD-049 `RecordProtectionOutcomeEvidence` | case/version, tipo, perfil/version, referencia, tiempos, identidad, regla, supersedes opcional, key | outcome ID/version, evaluación, brechas | evidence/profile/period/identity invalid, contradiction, stale, supersession conflict, idempotency conflict |
| CMD-050 `CloseProfitabilityProtectionCase` | case/version, outcome vigente, snapshot vigente, closure kind, brecha tipificada, key | case/version, cierre y brechas | errores exactos de la matriz §7, stale, idempotency conflict |
| QRY-030 `RetrieveProtectionOutcomeAssessment` | case ID, filtros de versión | outcome, procedencia minimizada, snapshot y brechas | concealed/not found/unauthorized |

Los IDs se verificaron libres en la base, pero permanecen sin registrar ni
reservar. QRY-028/029 conservan su semántica C3. No se propone EVT.

## 11. Persistencia y migración candidata

`20261105_59_netpay_protection_outcomes.py`, descendiente directa de 58, podría
crear:

- `netpay_protection_outcome_evidence` append-only;
- `netpay_protection_outcome_assessments` append-only/superseding;
- `netpay_protection_financial_snapshots` append-only/superseding;
- receipts C4 reutilizando o especializando la unicidad C3.

También debe reemplazar de forma reversible el check de estado del caso para
agregar únicamente `reactivation_verified`, `equipment_return_verified` y
`closed`; conserva todos los estados C3 y no introduce estados financieros como
estado del caso.

Campos: Organization, case/version, tipo/catálogo versionado, referencias
opacas, tiempos, periodo, moneda, Decimal, certeza, regla/version, componentes,
supersedes, actor y correlación. Se excluyen bytes, PII, contacto, notas libres,
cuentas bancarias y confirmación de caja. Este borrador no crea la migración.

La migración debe incluir FK de supersesión dentro del mismo tipo lógico,
unicidad de `supersedes_id`, fingerprints de atribución únicos por componente
vigente, checks de moneda/escala/certeza y triggers append-only para las tres
familias. La revisión vigente se consulta por anti-join contra sucesores, no por
UPDATE de una bandera. Downgrade elimina triggers, constraints y tablas en orden
inverso únicamente en la base local desechable.

## 12. Pruebas sintéticas obligatorias

### Evidencia y significado

- compromiso, llamada y solicitud no producen outcome;
- reactivación exacta válida pasa; Store-only queda supported;
- actividad anterior, futura, fuera de vigencia o contradictoria falla;
- recepción exacta pasa; guía/recolección/tránsito no verifica devolución;
- identidad ausente o cruzada entre tenants se rechaza/oculta;
- evidencia supersedida recalcula sin borrar histórico.
- corrección posterior al cierre conserva el cierre, marca evaluación stale y
  permite caso sucesor sólo por CMD-045 autorizado;
- dos supersesiones concurrentes producen un ganador y conflicto determinista.

### Finanzas

- movimiento comparable firmado y Decimal conserva signo/moneda;
- concepto no comparable y movimiento sin Store permanecen fuera y visibles;
- ausencia con fuente incompleta no prueba no recurrencia;
- ventana completa produce supported, nunca caja confirmada;
- crédito/reversión atribuible se calcula sin doble conteo;
- moneda, periodo, base o componente ausente produce no calculable;
- componentes solapados, precisión perdida o certeza elevada fallan;
- neto reportado, AS, promesa y outcome operativo no se presentan como dinero.
- AP+AQ+AR conserva comisión, AS conserva beneficio total combinado y ausentes
  no se convierten en cero;
- fórmulas v1, `ROUND_HALF_EVEN`, escala, certeza mínima y atribución producen el
  mismo snapshot en ejecuciones repetidas;
- un fingerprint no participa en dos componentes y solapamientos transitivos se
  rechazan.

### Integridad y autoridad

- replay byte-equivalente e idempotency conflict;
- carreras de evidencia y cierre tienen un ganador y respuesta determinista;
- stale version no conserva mutación parcial;
- receipts de conflicto se persisten sólo después de rollback de negocio y una
  falla inyectada nunca deja receipt o mutación parcial;
- UPDATE y DELETE de evidence/assessment/snapshot son rechazados;
- selección de hoja vigente funciona sin `is_current`, rechaza ciclos,
  bifurcaciones y supersesión cross-tenant;
- permisos positivos/negativos desde envelope del servidor;
- aislamiento tenant, minimización, PII ausente de respuesta/log/error/receipt;
- cero eventos, contacto, cache sensible y escrituras externas.

### Migración y regresión

- head único; 58→59→58→59 en PostgreSQL local tmpfs sin puertos;
- constraints, índices parciales y triggers reversibles;
- C1–C3, IG-015 e IG-016 A/B permanecen verdes;
- Ruff, compilación y `git diff --check` sobre bytes finales.

## 13. Resultado del gate

Estado vigente: **PASS LOCAL SINTÉTICO — 2026-11-06**. La implementación local,
migración 59 y los tres contratos autorizados cumplieron los criterios
ejecutables con fixtures sintéticos. Evidencia:
[IG-016A C4 local](evidence/netpay-ig016a-c4-local-20261106.txt).

- **PASS:** todos los criterios ejecutados localmente con fixtures sintéticos,
  sin inferencia, doble conteo, PII o efectos externos.
- **FAIL:** outcome sin evidencia suficiente, dinero/caja inferidos, pérdida de
  procedencia, mutación histórica, fuga tenant/PII o concurrencia no determinista.
- **BLOCKED:** falta decisión de autoridad de fuente, perfil, comparabilidad,
  ventana o semántica financiera necesaria para el caso evaluado.

Un PASS local no abre piloto, fuente real, importación, frontend, producción o
despliegue.

## 14. Decisiones que requieren ratificación de negocio/autoridad

1. Fuente y perfil autorizados para actividad posterior que verifica
   reactivación.
2. Fuente autoritativa de recepción/inventario y estados receptores válidos.
3. Mapa versionado de conceptos comparables, ventana completa y regla de importe
   esperado para penalización evitada.
4. Evidencia financiera certificada que permite elevar `supported` a
   `confirmed`; banco queda separado.
5. Si existe un consumidor real que justifique un EVT futuro. El default es no
   registrar evento.

Los detalles ordinarios de esquema, índices, nombres internos y fixtures pueden
resolverse durante implementación sin cambiar estas decisiones.

## 15. Indispensable para un piloto operativo posterior

- decisiones de §14 ratificadas y fuentes reales identificadas por perfil/hash;
- vínculos reales con temporalidad vigente y checkpoint humano;
- migración y contratos publicados después de validación local;
- ruta operativa/API y experiencia mínima autorizadas por separado;
- permisos, auditoría, observabilidad, rollback y UAT comprobados;
- autorización explícita de importación, migración y despliegue.

No se crea una fase C adicional por defecto. Estos requisitos son gates de
entrada al piloto, no autoridad operativa.

## 16. Exclusiones

Fuentes reales; importación; reprocesamiento; contacto; frontend; eventos;
mensajería; exportación; ledger; banco; producción; despliegue; migración
productiva; OIDC; roles; grants; capabilities; staging; commit y push.
