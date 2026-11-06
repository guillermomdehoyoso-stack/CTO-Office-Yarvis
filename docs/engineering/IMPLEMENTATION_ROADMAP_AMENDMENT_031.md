# Amendment 031 — IG-016A C3 casos, cola y contacto protegido

**RATIFIED — C3 LOCAL SYNTHETIC IMPLEMENTATION ONLY**

Fecha: 2026-11-02

Base verificada: `afb95a537784fd30b49b28e62b3ea179a2944842`

Ratificación: 2026-11-05. Se aprobaron los bytes de propuesta identificados por
SHA-256 `AFAC8A038924F96D352BD0BAC8012B4A1A4CE4494744DE305444410ED03B6938`.
La autoridad abre únicamente implementación y validación local sintética C3,
migración 58 y registro de CMD-044..048 y QRY-027..029. No autoriza EVT,
contratos adicionales, fuentes o contacto reales, staging, commit o push.

Autorización subordinada:
[IG-016A C3](IG-016A_C3_CASE_QUEUE_AND_PROTECTED_CONTACT_AUTHORIZATION.md)

## 1. Decisión ratificada

Se ratifica una autorización independiente y limitada para C3 de IG-016A. La
decisión abre sólo implementación local y pruebas sintéticas de casos,
cola minimizada, planificación humana y contacto protegido. C1 y C2 permanecen
cerrados como PASS publicados; C4 continúa cerrado.

Esta ratificación no autoriza fuentes reales, contacto real, importación,
despliegue, commit o push, ni contratos fuera del mapa aprobado.

## 2. Definición canónica de C3

La autoridad superior es Amendment 029 / IG-016. Su Gate C exige No Uso y cola
con estados y transiciones, replay, concurrencia y cierre operativo verificable.
Amendment 030 / IG-016A subdivide ese trabajo: C3 cubre contacto protegido,
casos, asignación, estados, acciones y cola; C4 conserva outcomes y validación
financiera. Por tanto C3 termina en historial operativo seguro y nunca declara
reactivación, devolución, penalización evitada o recuperación financiera.

Los 20 vínculos publicados por C2 siguen `pending/pending_temporality`. C3 puede
mostrarlos en una cola de identidad pendiente, pero no promoverlos a
`ready_to_contact`, abrir contacto ni inferir vigencia. Los 12 Stores sin equipo
y los 18 equipos sin Store/cliente siguen como excepciones, no como comercios
asignados.

## 3. Discrepancia contractual resuelta

IG-016 propuso estos significados:

- CMD-044 `ResolveStoreEquipmentLink`;
- CMD-045 `OpenProfitabilityProtectionCase`;
- QRY-027 `RetrieveStoreEquipmentIdentity`;
- EVT-032 `StoreEquipmentIdentityResolved`.

La revisión subordinada de IG-016A había reutilizado CMD-044, CMD-045, QRY-027
y EVT-032 para casos, acciones y cola. La ratificación resolvió la discrepancia
mediante el mapa reconciliado siguiente y excluyó todo EVT.

El mapa candidato reconciliado conserva las semánticas de IG-016 y desplaza la
cola/detalle a queries todavía no consumidas:

| ID candidato | Semántica C3 propuesta | Autoridad mínima |
| --- | --- | --- |
| CMD-044 | `ResolveStoreEquipmentLink` | inbox manage + reconciliation read |
| CMD-045 | `OpenProfitabilityProtectionCase` | inbox manage + reconciliation read |
| CMD-046 | `AssignAndPlanProtectionCase` | inbox manage |
| CMD-047 | `RecordProtectionContactAttempt` | inbox manage + sensitive read |
| CMD-048 | `DecideEquipmentRecoveryPath` | inbox manage |
| QRY-027 | `RetrieveStoreEquipmentIdentity` | reconciliation read |
| QRY-028 | `ListProfitabilityProtectionCases` | portfolio read |
| QRY-029 | `RetrieveProfitabilityProtectionCase` | portfolio read siempre; sensitive read + operations operator para contacto |

CMD-049/050 y las antiguas propuestas financieras de QRY-028/029 quedan
aplazadas y deberán recibir IDs distintos en C4. EVT-031+ permanecen libres: no
se demostró consumidor real para C3 y el historial interno append-only cubre la
auditoría local. La ratificación registra exactamente esta asignación local; no
registra EVT ni contratos adicionales.

## 4. Alcance ratificado

- caso tenant-scoped originado sólo desde lote/enlace C2 existente;
- estados `identity_pending`, `contact_pending`, `ready_to_contact`,
  `contact_attempted`, `reactivation_agreed`, `return_requested`, `monitoring`,
  `escalated` y `unrecoverable`;
- transición humana con `expected_version`, idempotency key y fingerprint;
- responsable, próxima acción y fecha compromiso, sin copiar PII;
- historial append-only con actor, estado anterior/nuevo, razón segura,
  correlación, causación y referencias opacas de evidencia;
- cola/listado minimizado tenant-scoped;
- detalle sensible separado, purpose-bound y auditado;
- acceso a contacto mediante Master, sin duplicarlo en el caso;
- matriz positiva y negativa de permisos vigentes;
- migración candidata posterior a revisión 57, sólo si la ratificación la
  identifica expresamente y el grafo sigue teniendo un head.

## 5. Exclusiones

- promover `pending_temporality` sin evidencia temporal ratificada;
- crear o inferir Store, terminal, serie, MID, cliente o contacto;
- importar o persistir los reportes reales;
- mensajería, llamadas o contacto automático;
- exportación masiva o PII en cola, logs, eventos, errores, receipts o notas;
- outcomes C4, reactivación verificada, equipo recibido, penalización eliminada,
  importe recuperado o cierre financiero;
- tasas, spread, tendencias, históricos reprocesados o caja bancaria;
- frontend, producción, despliegue, OIDC, roles, grants o capabilities nuevos;
- commit o push sin autorización posterior.

## 6. Condiciones previas a ratificar implementación

1. Aprobar el mapa contractual candidato y confirmar nuevamente los IDs libres.
2. Ratificar la matriz vigente: `netpay_operations_operator` es el único rol que
   reúne Inbox manage, Portfolio read, sensitive read y reconciliation read;
   `netpay_inbox_portfolio_reader` no puede consultar contacto ni excepciones.
   Si esta separación no basta, abrir Governance separado.
3. Definir qué evidencia temporal permite salir de `identity_pending`; hasta
   entonces los 20 vínculos reales no son contactables.
4. Ratificar catálogos cerrados para razones, próximas acciones, canales,
   resultados, decisiones y escalaciones; C3 no admite texto libre.
5. Revalidar el head de Alembic y el identificador de migración al ratificar.

### Política temporal exclusivamente sintética

Las pruebas C3 pueden usar únicamente fixtures con perfil
`synthetic_c3_temporality_v1`, link sintético, `observed_at`, `valid_from`,
`valid_to` opcional y procedencia `synthetic_fixture`. La ventana debe incluir el
instante de la acción. El intervalo es semiabierto: `valid_from <= action_at` y,
cuando existe, `action_at < valid_to`; además `valid_to` debe ser estrictamente
posterior a `valid_from`. Fechas invertidas, ventanas vacías, acciones anteriores
o posteriores a la ventana y timestamps sin zona se rechazan. El perfil se
rechaza fuera de PostgreSQL local desechable y no puede referenciar hashes,
batches o links de las tres fuentes reales. Los 20 links C2 reales permanecen
`pending_temporality` y no contactables.

### Contacto protegido

QRY-029 requiere siempre `netpay.portfolio.read`. Su proyección sensible requiere
además `netpay.portfolio.sensitive.read`, `purpose_code` de catálogo y auditoría.
El runtime exige permisos del `IdentityAuthorityEnvelope` resueltos por el
servidor. `netpay_operations_operator` describe la única matriz vigente que reúne
esa conjunción; no se agrega un campo de rol al request ni se confía en un rol,
grant o permiso declarado por el cliente. Cada lectura y CMD-047 revalida en Master
Organization, referencias activas, versión y disponibilidad; nunca confía en un
booleano persistido. La consulta puede emitir una referencia opaca de acceso,
vigente máximo cinco minutos y ligada a actor, Organization, caso, propósito y
versión Master, sin contener contacto.

### Concurrencia determinista

- misma key + mismo fingerprint: replay exacto de status/body original;
- misma key + fingerprint distinto: `idempotency_conflict` sin mutación;
- keys distintas abriendo la misma unicidad: un `created`; el perdedor obtiene
  `case_already_exists` con case ID/versión minimizados;
- keys distintas sobre la misma expected version: un ganador; el perdedor
  obtiene `stale_version` con versión actual minimizada;
- cada resultado, incluido conflicto determinista, conserva receipt seguro;
- `idempotency_conflict`, `case_already_exists` y `stale_version` no conservan
  cambio parcial de caso o historial: el receipt seguro y la respuesta
  determinista se producen sin mutación de negocio del intento perdedor.

## 7. Retención candidata

- caso, historial y referencias opacas: 24 meses desde estado terminal o
  supersesión;
- receipts idempotentes y auditoría de acceso sensible: 24 meses;
- contacto consultado: cero retención en caso, historial, receipt o evento;
- texto libre: prohibido; razones, planes, canales, resultados y decisiones usan
  catálogos cerrados y versionados;
- no existe purga en C3: cualquier eliminación posterior requiere política y
  operación gobernadas que preserven tombstone y conteos de auditoría.

## 8. Resultado local

C3 quedó **PASS local sintético** el 2026-11-05. La revisión `20261102_58`
desciende de 57 y pasó upgrade/downgrade/re-upgrade en PostgreSQL tmpfs. Se
registraron únicamente CMD-044..048 y QRY-027..029; no se registró EVT. Ruff,
compilación, 17 pruebas enfocadas y una regresión consolidada de 94 pruebas
pasaron sobre los bytes finales. C4, fuentes y contacto reales, frontend,
producción, staging, commit y push continúan cerrados.
