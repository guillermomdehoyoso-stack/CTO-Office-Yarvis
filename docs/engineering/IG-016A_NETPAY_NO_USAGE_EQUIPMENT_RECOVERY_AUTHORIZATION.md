# IG-016A — No Uso, identidad de equipos y recuperación de rentabilidad

**RATIFIED — C1 AND C2 LOCAL IMPLEMENTATION AND VALIDATION ONLY**

Fecha: 2026-11-01

Roadmap propuesto: [Amendment 030](IMPLEMENTATION_ROADMAP_AMENDMENT_030.md)

Dependencias: Amendment 029 / IG-016; Gate A PASS; Gate B PASS sintético; Gate
G PASS CON BRECHAS. Gates C–F, H e I continúan cerrados.

Revisión de perfiles y contratos:
[2026-11-01](NETPAY_IG016A_SOURCE_PROFILE_AND_CONTRACT_REVIEW_20261101.md)

## 1. Propósito

Diseñar un flujo gobernado que caracterice terminales sin uso, mantenga
identidad y temporalidad explícitas, permita una decisión humana entre
reactivación y devolución y verifique después el resultado operativo y
financiero sin doble contabilización.

Ratificado el 2026-11-01 para C1 y, mediante decisión separada, C2 local. C3–C4 permanecen cerrados. La denominación
IG-016A es válida porque Amendment 029 ya la define como subpaquete de IG-016; no consume un nuevo
IG numérico.

## 2. Invariantes

1. Store exacto es la única clave comercial.
2. Terminal, serie, MID y TID son identidades distintas.
3. `NA`, `#N/A`, vacío y cero no son equivalentes.
4. No se crea Store, cliente, contacto, MID o TID ausente.
   En Ticket v1, `Client ID` cero numerico o cadena exacta `0` tras trim es ausencia de cliente; no aplica a otras identidades o perfiles.
5. Global y Ticket son lotes independientes; Ticket enriquece y no sustituye.
6. Un vínculo exacto sin vigencia es evidencia histórica, no asignación actual.
7. Preview, aceptación y activación son decisiones separadas.
8. PII completa sólo es accesible a `netpay_operations_operator`.
9. Una acción prometida no es un outcome verificado.
10. Un componente financiero participa una sola vez.

## 3. Estado inicial derivado de Gate G

| Grupo | Tratamiento de diseño |
| --- | --- |
| 20 Stores con cadena exacta | identidad de lote evidenciada; link `pending` con razón `pending_temporality`; no contactable hasta checkpoint temporal |
| 12 Stores sin Global/Ticket | `missing_equipment_match`; cola de identidad, nunca caso contactable |
| 18 equipos sin Store ni cliente | `missing_store_and_client`; equipo visible en reconciliación, nunca asignado |
| 209 observaciones `NA` | `placeholder`; conservadas en métricas de preview, sin identidad |
| 18 `#N/A` en `ESTADO` | `cell_error`; dirección incompleta, sin invalidar identidad de equipo |
| 0 MID/TID explícitos | campos ausentes; ningún derivado desde Store o terminal |

No se detectaron ambiguos o contradictorios en esos tres lotes. El diseño debe
seguir soportándolos porque otro lote puede producirlos.

## 4. Estados de identidad

Se reutiliza el modelo publicado:

- `pending`: identidad o temporalidad insuficiente;
- `confirmed`: relación exacta con intervalo o corte autorizado;
- `ambiguous`: más de un candidato exacto compatible;
- `contradictory`: evidencia simultánea incompatible;
- `superseded`: resolución posterior que preserva historia.

`pending_temporality` es razón normalizada de `pending`, no un nuevo estado de
base. Los 20 vínculos de Gate G sólo pueden llegar a `confirmed` tras evidencia
de corte/vigencia o decisión humana autorizada que cite evidencia temporal.

## 5. Clasificación de fila

Cada preview produce una clasificación y razones acumulables:

| Clasificación | Condición |
| --- | --- |
| `candidate` | fila de negocio con campos mínimos del perfil |
| `excluded` | `template_row` o `placeholder` sin identidad accionable |
| `pending` | falta Store, equipo, cliente, temporalidad o campo requerido resoluble |
| `invalid` | firma incompatible, tipo inválido o error material |
| `ambiguous` | dos o más correspondencias exactas candidatas |
| `contradictory` | identidades exactas incompatibles |

Razones propuestas: `placeholder`, `cell_error`, `blank`, `template_row`,
`missing_store`, `missing_equipment`, `missing_client`,
`missing_temporality`, `unsupported_value`, `ambiguous_identity` y
`contradictory_identity`. Los nombres finales deben alinearse con errores
vigentes antes de implementación.

## 6. Pipeline y checkpoints

### Preview

Recibe bytes y perfil solicitado; calcula hash; valida ZIP/OOXML, firma,
encabezados, tipos y límites; clasifica y normaliza en memoria; calcula métricas
y devuelve un `preview_token` opaco. No crea lote, fila, identidad o receipt.

### Checkpoint humano

Muestra hash, perfil, conteos, temporalidad ausente, exactos, pendientes,
ambiguos, contradictorios, excluidos y campos PII disponibles. El actor decide
rechazar, solicitar corrección o aceptar. No puede cambiar filas ni declarar
vigencia desde el nombre del archivo.

### Aceptación

Revalida bytes, hash, perfil, `preview_token`, estado de Store y expected
version. Usa idempotency key sin PII. Persiste lote/filas/procedencia e identidades
permitidas, mantiene temporalidad pendiente y devuelve readback. Replay idéntico
devuelve el mismo resultado; misma clave con payload distinto es conflicto.

### Activación operativa

Es una decisión posterior de C3. Sólo links con temporalidad suficiente,
cliente canónico y contacto autorizado pueden abrir `ready_to_contact`. Aceptar
un lote nunca contacta ni abre automáticamente un caso contactable.

## 7. Caso de recuperación

Campos mínimos:

- Organization y versión;
- StoreReference opcional y link de equipo;
- terminal/serie y MID/TID opcionales por identidad separada;
- lote, hoja, fila y evidencia;
- referencia canónica a Client/Company/Branch, sin copiar PII;
- `contact_available` y fuente/scope;
- motivo y certeza;
- penalización aplicada o probable con periodo/concepto/procedencia cuando exista;
- responsable, acción recomendada, próxima acción y fecha compromiso;
- estado e historial append-only;
- expected version, correlación, causación e idempotencia.

Estados propuestos:

```text
identity_pending
ready_to_contact
contact_attempted
reactivation_agreed
return_requested
monitoring
reactivated_verified
equipment_returned
escalated
closed
unrecoverable
```

`identity_pending` no permite contacto. `ready_to_contact` exige link vigente,
cliente canónico y acceso autorizado. `closed` y `unrecoverable` son terminales;
reapertura futura sería supersesión, no edición.

## 8. Transiciones mínimas

| Desde | Hacia | Evidencia mínima |
| --- | --- | --- |
| `identity_pending` | `ready_to_contact` | Store–equipo vigente, cliente canónico y contacto disponible |
| `ready_to_contact` | `contact_attempted` | actor, canal tipificado y resultado seguro; sin PII en evento |
| `contact_attempted` | `reactivation_agreed` | compromiso humano y fecha; aún no verifica reactivación |
| `contact_attempted` | `return_requested` | decisión humana y equipo exacto; aún no prueba recepción |
| acuerdos/solicitudes | `monitoring` | ventana y próxima verificación |
| `monitoring` | `reactivated_verified` | actividad posterior compatible con identidad y corte |
| `monitoring` | `equipment_returned` | recepción/inventario con terminal o serie exacta |
| cualquier no terminal | `escalated` | bloqueo y responsable explícitos |
| verificados | `closed` | resultado financiero evaluado o brecha declarada |
| no terminal | `unrecoverable` | razón y evidencia humana |

## 9. Cierre y finanzas

| Resultado | Evidencia exigida |
| --- | --- |
| reactivación verificada | transacción/actividad posterior, identidad compatible y fecha posterior al compromiso |
| equipo devuelto | recepción o inventario con terminal/serie exacta; solicitud no basta |
| penalización eliminada | mapa de concepto aprobado y ventana posterior definida sin repetición, o confirmación del emisor |
| penalización evitada | regla contrafactual versionada, periodo comparable y acción verificada; normalmente `projected` |
| importe recuperado | mejora observada posterior, base compatible, atribución declarada y componentes no superpuestos |

Penalización aplicada requiere movimiento firmado comparable. Penalización
probable permanece separada. La ausencia en un solo archivo no demuestra
causalidad. Neto reportado para pago no equivale a depósito bancario.

## 10. Privacidad y autoridad

- Cola general: Store, equipo minimizado, estado, responsable, fuente, motivo y
  presencia de contacto bajo `netpay.portfolio.read`.
- Excepciones seguras: `netpay.portfolio.reconciliation.read`.
- Contacto/RFC/domicilio/Client ID completo: sólo consulta explícita con
  `netpay.portfolio.sensitive.read` y rol `netpay_operations_operator`.
- Fuentes y mutaciones: `netpay.inbox.read/manage` conforme al patrón vigente.
- Acción de contacto: exige la conjunción `netpay.inbox.manage` +
  `netpay.portfolio.sensitive.read`.
- Logs, eventos, métricas, errores, idempotency keys y fixtures no contienen PII.
- Cada consulta/uso sensible registra actor, Organization, recurso, propósito,
  tiempo y correlación, sin copiar el valor consultado.
- Sin mensajería automática, exportación masiva o capability nueva inicial.

## 11. Contratos candidatos mínimos

| ID | Nombre | Gate | Actor / scope | Evento |
| --- | --- | --- | --- | --- |
| QRY-025 | `PreviewNoUsageRecoverySources` | C1 | operations operator; inbox manage | ninguno |
| CMD-043 | `AcceptNoUsageRecoverySource` | C2 | operations operator; inbox manage | historial interno; sin evento |
| QRY-026 | `RetrieveNoUsageSourceReview` | C2 | inbox read; reconciliation para excepciones | ninguno |
| CMD-044 | `OpenOrUpdateNoUsageRecoveryCase` | C3 | operations operator; inbox manage | EVT-032 |
| CMD-045 | `RecordNoUsageRecoveryAction` | C3 | operations operator; inbox manage; sensitive para contacto | EVT-032 |
| QRY-027 | `ListOrRetrieveNoUsageRecoveryCases` | C3 | portfolio read; sensitive detail separado | ninguno |
| CMD-046 | `VerifyNoUsageRecoveryOutcome` | C4 | operations operator; inbox manage | EVT-033 |

Los nombres completos usan prefijo `IC-NETPAY-`. No se registran aquí. Los
contratos detallados están en la revisión enlazada. No se reservan CMD-047..050,
QRY-028..029 o EVT-034..038.

## 12. Migración candidata

`20261031_57` desciende de `20261030_56` y está implementada sólo para C2. C1 no la
necesita. El diseño separa lotes, clasificaciones agregadas, excepciones, historial
y receipts; referencia Master para PII y reutiliza identidades/evidencia
de Gate B. Debe ser reversible y probar upgrade/downgrade/re-upgrade en
PostgreSQL aislado. No incluye tasas, spread ni tendencias.

## 13. Subgates y criterios

### C1 — perfiles y preview

PASS: tres perfiles deterministas, formatos incompatibles rechazados, métricas
Gate G reproducidas sin PII y cero escrituras. FAIL: pérdida de filas, `NA` como
identidad, `#N/A` como negocio o escritura. BLOCKED: bytes/perfil autorizado no
disponible. Rollback: retirar parser/query local; no hay datos.

### C2 — aceptación e identidad

PASS: checkpoint, hash, replay, concurrencia, lote único, filas/procedencia,
readback y links `pending_temporality` probados. FAIL: duplicación, vigencia
inferida o Store creado. BLOCKED: temporalidad/autoridad de aceptación no
ratificada o migración no aprobada. Rollback: downgrade sólo en base aislada y
sin datos externos; rechazo/supersesión en datos aceptados, nunca borrado oculto.

### C3 — contacto y cola

PASS: matriz positiva/negativa de scopes, PII auditada, estados, expected version,
concurrencia e historial pasan. FAIL: fuga, contacto desde `identity_pending`,
last-write-wins o evento con PII. BLOCKED: conjunción de autoridad no demostrable.
Rollback: desactivar rutas/feature local; casos preservados, no borrados.

### C4 — verificación financiera

PASS: reactivación, devolución, concepto comparable, ventanas, certeza y no doble
conteo pasan. FAIL: promesa tratada como outcome, ausencia única como causalidad
o caja inferida. BLOCKED: mapa de conceptos, periodos o evidencia de recepción
ausentes. Rollback: snapshots superseded; hechos fuente intactos.

## 14. Pruebas propuestas

- hashes exactos y archivo corregido con nueva huella;
- firmas incompatibles, hojas/headers reordenados o repetidos;
- filas de plantilla, `NA`, `#N/A`, blank y unsupported;
- Store exacto, Store ausente, equipo sin cliente y varios Stores por cliente;
- preview sin escrituras; checkpoint requerido;
- replay, conflicto de clave, concurrencia y no duplicación de casos;
- readback y procedencia hoja/fila;
- Organization extranjera, concealment, roles/scopes y errores sin PII;
- historial append-only y expected-version conflict;
- migración reversible y rollback por subgate;
- ventanas financieras, conceptos no comparables y componentes superpuestos.

No se usarán fixtures con PII real.

## 15. Decisiones pendientes

1. Corte/vigencia que permite promover `pending_temporality`.
2. Productor y contrato estable de los tres perfiles futuros.
3. Evidencia canónica de recepción/inventario.
4. Mapa versionado de conceptos de penalización No Uso.
5. Ventana mínima para no repetición y atribución financiera.
6. Política de retención de evidencia restringida y bytes descartados.
7. Una migración 57 integral o revisiones por C2/C3/C4.
8. Consumidor operativo real de EVT-031 y proyección de EVT-032/033.

## 16. Primera autorización recomendada

Ratificar solamente C1: tres perfiles y QRY-025 local, read-only, con fuentes
literales/hash allowlisted, sin persistencia, migración, contratos runtime,
frontend, contacto, commit o despliegue. C3–C4 permanecen cerrados.
