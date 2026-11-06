# IG-016A C3 — Casos, cola y contacto protegido

**RATIFIED — C3 LOCAL SYNTHETIC IMPLEMENTATION ONLY**

Fecha: 2026-11-02

Roadmap ratificado: [Amendment 031](IMPLEMENTATION_ROADMAP_AMENDMENT_031.md)

Base requerida: `afb95a537784fd30b49b28e62b3ea179a2944842`

Ratificación: 2026-11-05. Se aprobaron los bytes de propuesta identificados por
SHA-256 `3F9D0D5AEA9AE7946F828B9BCF0F60053960B0DD9DF8208E7C3111214D55889F`.
Quedan autorizados localmente migración 58 y los contratos CMD-044..048 y
QRY-027..029. No se autoriza EVT ni ningún contrato adicional.

Dependencias: C1 y C2 PASS publicados; migración `20261031_57`; C4 cerrado.

## 1. Objetivo

Autorizar un slice local de trabajo humano que convierta
evidencia C2 en casos y cola gobernados, mantenga identidad y temporalidad
explícitas, proteja el acceso a contacto y preserve historial. Aceptar una fuente
o abrir un caso no confirma asignación vigente ni resultado operativo.

## 2. Invariantes

1. Sólo se referencia un lote, excepción, StoreReference o link C2 existente.
2. `pending_temporality` permanece no contactable.
3. Store exacto es la única identidad comercial; nombres y PII no resuelven.
4. Contacto vive en Master y se consulta bajo autorización; no se copia al caso.
5. Listado, eventos, logs, errores, receipts e historial no contienen PII.
6. Cada mutación exige Organization, actor, expected version, idempotency key y
   fingerprint; concurrencia incompatible falla.
7. Replay idéntico devuelve la misma respuesta y una clave con otro payload es
   conflicto.
8. Historial es append-only; las correcciones superseden y no reescriben.
9. Una promesa, intento de contacto o solicitud de devolución no es outcome.
10. C3 no calcula ni declara efectos financieros.
11. La temporalidad habilitante de C3 existe sólo en fixtures sintéticos
    allowlisted; ninguna fuente real cambia de estado.
12. Todo motivo, plan, canal, resultado y decisión usa catálogo cerrado; no hay
    texto libre.

## 3. Modelo mínimo candidato

### Caso

- Organization, ID y aggregate version;
- referencia a batch/link/excepción C2;
- StoreReference opcional, sin Store inferido;
- estado y razón segura;
- responsable canónico opcional;
- próxima acción tipificada y fecha compromiso opcional;
- `contact_available` booleano, sin valor de contacto;
- timestamps, correlación y causación.

### Historial

- caso y versión;
- estado anterior/nuevo;
- tipo de cambio y razón segura;
- actor y tiempo;
- referencias opacas a evidencia;
- sin nota libre ni PII.

### Receipt

- Organization, command semantic ID, clave sin PII, fingerprint, case ID,
  versión y respuesta minimizada.

### Catálogos cerrados C3 v1

- `case_reason_code`: `no_usage`, `missing_equipment_match`,
  `missing_store_and_client`, `pending_temporality`;
- `next_action_code`: `resolve_identity`, `obtain_contact`, `contact_merchant`,
  `follow_up_reactivation`, `follow_up_return`, `escalate`;
- `contact_channel_code`: `phone`, `email`, `other_authorized`;
- `contact_result_code`: `reached`, `no_answer`, `invalid_contact`,
  `follow_up_required`;
- `recovery_path_code`: `reactivate`, `return_equipment`, `monitor`,
  `unrecoverable`;
- `escalation_reason_code`: `identity_blocked`, `contact_blocked`,
  `authority_blocked`, `business_decision_required`.

Los catálogos se versionan y validan por igualdad exacta. No existe `note`,
`comment`, `free_reason` ni campo equivalente.

### Política temporal sintética v1

Sólo fixtures allowlisted con perfil `synthetic_c3_temporality_v1` pueden probar
salida de `identity_pending`. El fixture incluye link sintético, `observed_at`,
`valid_from`, `valid_to` opcional y procedencia `synthetic_fixture`; la ventana
es semiabierta y debe cumplir `valid_from <= action_at` y, cuando existe,
`action_at < valid_to`; `valid_to` debe ser estrictamente posterior a
`valid_from`. Se rechazan fechas invertidas, ventanas vacías, acciones fuera de
la ventana y timestamps sin zona. Debe rechazarse fuera de PostgreSQL local
desechable y no puede usar hashes, batches, filas o links reales. Las 20
relaciones C2 reales permanecen `pending_temporality` y no contactables.

## 4. Estados y transiciones C3

| Desde | Hacia | Condición mínima |
| --- | --- | --- |
| creación | `identity_pending` | vínculo o excepción C2; sin vigencia suficiente |
| creación | `contact_pending` | identidad vigente evidenciada; contacto aún no disponible |
| `contact_pending` | `ready_to_contact` | identidad vigente y contacto disponible bajo Master |
| `identity_pending` | `contact_pending` | vínculo temporalmente soportado; contacto ausente |
| `identity_pending` | `ready_to_contact` | vínculo temporalmente soportado y contacto disponible |
| `ready_to_contact` | `contact_attempted` | actor autorizado, canal tipificado y resultado seguro |
| `contact_attempted` | `ready_to_contact` | reintento humano explícito con siguiente acción |
| `contact_attempted` | `reactivation_agreed` | compromiso humano y fecha; no outcome |
| `contact_attempted` | `return_requested` | decisión humana y equipo exacto; no recepción |
| `contact_attempted` | `monitoring` | seguimiento sin compromiso de reactivar/devolver |
| acuerdos/solicitudes | `monitoring` | ventana y próxima verificación |
| `monitoring` | `ready_to_contact` | nueva acción humana de contacto |
| `monitoring` | `contact_attempted` | intento posterior ya realizado y tipificado |
| cualquier no terminal | `escalated` | razón y responsable explícitos |
| `escalated` | estado previo compatible | resolución explícita y expected version vigente |
| cualquier no terminal | `unrecoverable` | razón humana evidenciada |

`identity_pending` no transiciona a estado contactable sin evidencia temporal
aceptada. `reactivated_verified`, `equipment_returned`, cierre financiero y
outcomes pertenecen a C4 y quedan ausentes del modelo C3.

`unrecoverable` es terminal dentro de C3. No existe transición a estados C4. Una
corrección posterior supersede el caso bajo autoridad futura; no reabre ni edita
el historial.

## 5. Unicidad y consistencia

- fuente de caso: `source_kind` (`link`, `batch_exception`) + `source_id`;
- causa normalizada obligatoria;
- máximo un caso no terminal por
  `(organization_id, source_kind, source_id, cause_code)`;
- la defensa final es un índice único parcial donde `terminal_at IS NULL`;
- un caso terminal no se reabre: una autorización futura crea sucesor con
  `supersedes_case_id`;
- Organization de caso, fuente, StoreReference, responsable y actor debe
  coincidir; referencia extranjera se oculta;
- cambio de responsable, plan o estado incrementa una única aggregate version y
  escribe historial + receipt en la misma transacción;
- dos claves distintas que compiten por la misma unicidad se serializan; el
  perdedor recibe el caso canónico o conflicto determinista, nunca un duplicado.

## 6. Mapa contractual candidato

| ID candidato | Nombre | Entrada mínima | Salida | Autoridad |
| --- | --- | --- | --- | --- |
| CMD-044 | `ResolveStoreEquipmentLink` | link/version, evidencia temporal, decisión, key | link/version y estado seguro | inbox manage + reconciliation read |
| CMD-045 | `OpenProfitabilityProtectionCase` | fuente C2, causa, expected source version, key | case ID/version/estado | inbox manage + reconciliation read |
| CMD-046 | `AssignAndPlanProtectionCase` | case/version, responsable, acción/fecha, key | case/version/plan seguro | inbox manage |
| CMD-047 | `RecordProtectionContactAttempt` | case/version, canal y resultado tipificados, key | case/version/estado | inbox manage + sensitive read |
| CMD-048 | `DecideEquipmentRecoveryPath` | case/version, reactivar/devolver/seguir/no recuperable, key | case/version/estado | inbox manage |
| QRY-027 | `RetrieveStoreEquipmentIdentity` | link/excepción | identidad y brechas minimizadas | reconciliation read |
| QRY-028 | `ListProfitabilityProtectionCases` | filtros/paginación seguros | cola minimizada | portfolio read |
| QRY-029 | `RetrieveProfitabilityProtectionCase` | case ID, `include_contact`, purpose code | detalle/historial; contacto sólo sensible | portfolio read siempre; sensitive read + operations operator para contacto |

Owner propuesto: Netpay Merchant Operations; capability: profitability
protection case handling. CMD-049/050 quedan para C4 con IDs por decidir. Las
propuestas anteriores de métricas/cobertura en QRY-028/029 quedan desplazadas y
requieren nueva decisión. No se propone EVT: no existe consumidor demostrado;
historial interno cubre auditoría. La ratificación de 2026-11-05 autoriza
registrar exactamente estos IDs como parte de C3; no registra EVT ni contratos
adicionales.

## 7. Seguridad y matriz de autoridad

- cola general: `netpay.portfolio.read`;
- excepciones de identidad: `netpay.portfolio.reconciliation.read`;
- mutaciones: `netpay.inbox.manage`;
- contacto completo: `netpay.portfolio.sensitive.read` y rol vigente
  `netpay_operations_operator`;
- cualquier acción que use contacto requiere la conjunción de mutación y lectura
  sensible, purpose explícito y auditoría sin valor PII;
- recurso extranjero se oculta conforme al patrón vigente.

No se propone rol, capability, grant u OIDC nuevo. Si la conjunción no puede
demostrarse con las reglas vigentes, C3 queda BLOCKED.

| Operación | `netpay_inbox_portfolio_reader` | `netpay_inbox_operator` | `netpay_operations_operator` |
| --- | --- | --- | --- |
| listar cola minimizada | permitir | denegar | permitir |
| ver identidad/excepciones | denegar | denegar | permitir |
| abrir desde excepción | denegar | denegar | permitir |
| asignar/planear sin PII | permitir | permitir | permitir |
| leer contacto completo | denegar | denegar | permitir con propósito/auditoría |
| registrar intento usando contacto | denegar | denegar | permitir con conjunción sensible |

Aunque `netpay_inbox_portfolio_reader` posee inbox manage, nunca recibe contacto
ni reconciliation. Las mutaciones que dependan de cualquiera de esos datos
requieren explícitamente la capacidad adicional y por ello quedan limitadas al
rol vigente `netpay_operations_operator`.

QRY-029 aplica una sola regla: todo request exige `netpay.portfolio.read`; si
`include_contact = true`, exige además `netpay.portfolio.sensitive.read`,
`purpose_code` de catálogo y auditoría segura. La comprobación usa exclusivamente
los permisos validados del `IdentityAuthorityEnvelope` resuelto por el servidor.
`netpay_operations_operator` identifica la única matriz vigente que contiene la
conjunción requerida; el request no incorpora un campo de rol y nunca se acepta
un rol, grant o permiso declarado por el cliente.
Cada QRY-029 sensible y cada CMD-047 revalida directamente en Master la misma
Organization, referencias activas, versión y disponibilidad. No se autoriza por
el booleano persistido `contact_available`. QRY-029 puede devolver una referencia
opaca de acceso válida máximo cinco minutos, ligada a actor, Organization, caso,
purpose y versión Master; CMD-047 rechaza referencia vencida o desactualizada.

## 8. Retención

- caso, historial y referencias opacas: 24 meses desde terminal/superseded;
- receipts y auditoría de acceso sensible: 24 meses;
- contacto: sólo respuesta sensible puntual; no cache ni persistencia C3;
- `contact_available` es sólo un indicador observado con fuente/instante y nunca
  prueba autorización o vigencia;
- canales, resultados, razones, acciones, decisiones y escalaciones usan los
  catálogos cerrados C3 v1; no se persiste texto libre;
- no se persiste dirección, teléfono, correo ni Client ID externo;
- no hay purga implementada en C3; una política posterior debe conservar
  tombstone, conteos y prueba de autorización.

## 9. Persistencia y migración

Una ratificación posterior puede autorizar una revisión descendiente directa de
57 para caso, historial append-only y receipts. Debe excluir fuentes/bytes,
contacto, casos C4, outcomes, tasas, spread y tendencias. El identificador se
elige sólo tras revalidar el grafo; `20261102_58` es candidato, no reserva.

Downgrade sólo se prueba en PostgreSQL local desechable. Si existen casos
aceptados, una futura política operativa deberá superseder/desactivar, no borrar
historia silenciosamente.

## 10. Criterios de aceptación

### Funcionales

- caso único por causa/link bajo la regla ratificada;
- los 20 links C2 siguen `identity_pending` mientras falte temporalidad;
- 12 Stores y 18 equipos pendientes permanecen visibles y sin asignación;
- transiciones válidas pasan y las inválidas fallan;
- ningún estado C4 existe o puede alcanzarse.
- unicidad parcial impide dos casos activos para la misma fuente/causa;
- un caso terminal sólo puede tener sucesor, nunca reapertura in-place.

### Idempotencia y concurrencia

- primera ejecución válida devuelve `created` o `transition_applied`;
- misma key y mismo fingerprint repite exactamente status y body originales;
- misma key con otro fingerprint devuelve `idempotency_conflict`, sin mutación;
- keys distintas que abren la misma unicidad producen un `created`; el perdedor
  devuelve `case_already_exists` con case ID/versión minimizados;
- keys distintas con la misma expected version producen un ganador; el perdedor
  devuelve `stale_version` con versión actual minimizada;
- cada resultado, incluido conflicto, conserva receipt seguro para replay;
- `idempotency_conflict`, `case_already_exists` y `stale_version` no conservan
  cambios parciales del caso o historial; sólo registran el receipt seguro y la
  respuesta determinista del intento perdedor;
- cualquier otro fallo parcial revierte caso, historial y receipt juntos;
- trigger impide UPDATE/DELETE de historial.

### Seguridad y privacidad

- matriz positiva/negativa de los cuatro permisos vigentes;
- tenant extranjero se oculta;
- cola y detalle no sensible no exponen contacto;
- lectura sensible requiere conjunción, propósito y auditoría;
- PII ausente de logs, eventos, errores, receipts, fixtures e idempotency keys;
- no hay exportación o contacto automático.
- portfolio reader e inbox operator fallan en lectura sensible, reconciliación y
  contacto; operations operator pasa sólo con propósito y auditoría.

### Retención y minimización

- casos/history/receipts declaran timestamps y política de 24 meses;
- ninguna tabla contiene valor de contacto o Client ID externo;
- un código fuera del catálogo o versión desconocida se rechaza como
  `unsupported_catalog_value`, sin eco del input;
- serialización de respuesta, errores y auditoría no reproduce valores sensibles;
- no existe job de purga, exportación ni cache sensible en C3.

### Migración y regresión

- un solo head; upgrade/downgrade/re-upgrade en base desechable;
- constraints tenant-scoped y triggers reversibles;
- C1/C2, IG-014, IG-015 e IG-016 A/B permanecen verdes;
- Ruff, compilación y `git diff --check` pasan sobre bytes finales.

### Pruebas sintéticas mínimas

- creación por link y por excepción; tenant extranjero y fuente inexistente;
- un fixture sintético de 20 relaciones pending sólo crea `identity_pending`;
- los 20 links reales no se leen, copian ni modifican;
- perfil temporal sintético válido, vencido, futuro, sin intervalo y usado fuera
  del entorno aislado;
- cobertura completa de cada transición permitida y cada transición ausente;
- respuestas exactas `created`, `case_already_exists`, `transition_applied`,
  `idempotency_conflict` y `stale_version` bajo carreras repetidas;
- replay byte-equivalente, receipts de conflictos y rollback parcial;
- historial UPDATE/DELETE rechazado después de re-upgrade;
- matriz de roles/scopes por cada contrato y field-level redaction;
- QRY-029 base/sensible, purpose vacío, rol incorrecto, referencia de contacto
  vencida, versión Master cambiada y auditoría minimizada;
- cada catálogo válido, código desconocido, versión desconocida y ausencia total
  de campos de texto libre;
- paginación/sort/filtros, conteos sin fuga y concealment cross-tenant;
- C1/C2, IG-014, IG-015 e IG-016 A/B como regresión obligatoria.

## 11. Resultado del gate

Estado vigente: **PASS LOCAL SINTÉTICO — 2026-11-05**. El resultado comprende
servicios locales, persistencia, migración 58, los ocho contratos ratificados y
pruebas sintéticas. No constituye activación operativa ni abre C4.

- **PASS:** todos los criterios ejecutados sobre implementación local aislada,
  sin PII ni efectos externos.
- **FAIL:** fuga, contacto desde identidad pendiente, inferencia de identidad,
  last-write-wins, historia mutable o estado C4.
- **BLOCKED:** mapa contractual, temporalidad o autoridad sensible no resueltos.

## 12. Exclusiones expresas

Fuentes reales, importación, contacto real, frontend, mensajería, exportación,
producción, despliegue, activación, migración productiva, OIDC, roles, grants,
capabilities, C4, finanzas, commit y push.

## 13. Cierre técnico local

La ratificación fue ejecutada exclusivamente en el alcance autorizado. Evidencia:
[IG-016A C3 local](evidence/netpay-ig016a-c3-local-20261105.txt). Cualquier
publicación, endpoint operativo, fuente real, contacto real o C4 requiere una
decisión posterior independiente.
