# Netpay MVP-2D1 Manual Review Variant — borrador de ratificación independiente

## Estado y efecto

**BORRADOR PARA APROBACIÓN HUMANA — NO RATIFICADO — NO ES UNA AUTORIZACIÓN DE IMPLEMENTACIÓN.**

Este documento propone la ratificación independiente de **MVP-2D1 Manual Review
Variant**. No modifica el catálogo canónico de contratos, los contratos ya
ratificados, código, esquemas, migraciones, configuración ni secretos. Su
eventual ratificación fijaría decisiones de arquitectura y la reserva propuesta
de identidades; una autorización de implementación posterior sigue siendo
obligatoria y separada.

La decisión se apoya en la Constitución, en la autoridad explícita de
Principal + organización activa + membresía + permisos persistidos, en el
contrato de Inbox de `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` (ratificado y
con exclusión expresa de Gmail/sincronización), y en el diseño
`NETPAY_MVP2D_GMAIL_INTAKE_DESIGN.md`. Gmail es evidencia externa; no es
identidad, autoridad ni verdad canónica.

## 1. Base de evidencia y corrección de referencia

La base aceptada, comprobada localmente, es:

| Elemento | Valor exacto |
| --- | --- |
| Rama base | `feat/netpay-operational-radar` |
| Commit base | `50cbb26e1828a711382cb35818b722eb69a04ce2` |
| Alembic presente | `20260814_39` |
| Padre documental posterior | `5406b2485957e078bb7dd426986e5098b8529461` |

Toda referencia anterior a `50cbb26e1828a711382cb358b722eb69a04ce2` es
incorrecta: ese objeto no existe. La única referencia válida para esta
ratificación es el SHA con `...35818b...` indicado arriba.

## 2. Decisión propuesta, sustitución acotada y alcance exacto

Esta **MVP-2D1 Manual Review Variant** sustituye únicamente la definición D1 de
`NETPAY_MVP2D_GMAIL_INTAKE_DESIGN.md` para el alcance Gmail de
`Distribución Netpay` y el buzón explícito de este documento. Sustituye la
definición D1 original de OAuth/configuración sin revisión por un corte de
revisión manual sin OAuth real ni recursos externos. No modifica otros
buzones, tenants, proveedores, las fases D2–D5,
`IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`, F-011, Radar,
ni contratos/catálogos canónicos existentes.

Se propone un único corte de sólo lectura, ejecutado únicamente por activación
humana autorizada, que preserva evidencia candidata aislada por organización.
No crea, actualiza, transiciona ni cierra automáticamente un
`NetpayServiceCase`, ni modifica Netpay Master, Radar, Document Registry,
Mission Work u Operational Task.

La revisión humana puede corregir, marcar para revisión, descartar o marcar un
candidato como duplicado. La aceptación que componga `IC-NETPAY-CMD-009` queda
**íntegramente diferida a MVP-2D2**: no se asigna, reserva ni autoriza en esta
variante. Una propuesta posterior deberá abrir explícitamente ese corte y volver
a validar los permisos Inbox/Master. Ninguna sugerencia o resultado de correo
constituye confirmación humana.

## 3. Parámetros operativos decididos para la ratificación

Los identificadores operativos y las restricciones de esta tabla se registran
como decisiones humanas; su realización técnica sigue prohibida hasta el
mandato futuro definido en la sección 8.

| Parámetro | Decisión propuesta vinculante |
| --- | --- |
| 1. Buzón → tenant | Un solo buzón **dedicado**, `guillermo.dehoyos@netpay.com.mx`, identificado además por su `emailAddress` estable resuelto por el proveedor, se enlaza explícitamente y sólo con `Distribución Netpay` (`59650e6f-ad62-40c3-8cb0-7710a122ce8b`). El alta exige esa selección explícita; remitente, destinatario, dominio, contenido, header, claim, Store ID y workspace jamás infieren ni eligen la organización. Un mismo buzón no puede tener dos enlaces activos. |
| 2. Filtro inicial | `Yarvis/Netpay-Intake` es la configuración humana de nombre exacto. Una futura configuración debe resolver mediante Gmail su `label_id` canónico, persistir el **mailbox binding + label_id** y verificar ese `label_id` en cada sincronización. Un `label_id` ausente, inválido, ambiguo, eliminado o inconsistente con el binding bloquea fail-closed la sincronización: no hay fallback por nombre visible, consulta fuera del binding, candidatos ni avance de cursor; sólo puede registrarse evidencia sanitaria mínima y no sensible. Sólo se consideran mensajes que porten el `label_id` verificado. No se aplica allowlist de remitentes en esta variante; éstos sólo podrán elevar confianza mediante decisión posterior, nunca seleccionar tenant. |
| 3. Backfill | Ventana inicial máxima de **30 días calendario** anteriores al primer disparo manual, aplicada al mismo filtro. Ampliarla exige una nueva orden administrativa auditada; no alcanza los 62 registros históricos excluidos. |
| 4. Retención | La retención máxima ordinaria de cuerpo, extracto y metadatos no indispensables es de **90 días** desde la sincronización; el extracto de texto plano saneado nunca supera **4 KiB**. Al vencer, la política exige conservar sólo tombstone, hash, timestamps y constancia auditable de expurgo. Un legal hold futuro sólo puede suspender el expurgo por autoridad canónica explícita y debe registrar `scope`, `reason`, `authorized_by`, `started_at`, `review_at` y `expires_at`; esta ratificación no crea ni activa legal holds. Al vencer el hold vuelve a aplicar inmediatamente la política ordinaria. Si un expurgo obligatorio falla, la configuración entra en `retention_blocked`: detiene fail-closed nueva sincronización o ingestión, no avanza cursor, no crea candidatos y no permite extender silenciosamente la retención. La recuperación exige remediación, evidencia auditable y reautorización humana. Esta política puede ratificarse ahora, pero ninguna operación de hold, expurgo o recuperación se implementa en esta variante sin gate independiente; el futuro gate debe demostrar eliminación efectiva e idempotente. |
| 5. Roles y bootstrap propuesto | Se proponen `netpay_intake_viewer` (`netpay.intake.read`), `netpay_intake_reviewer` (`read`, `netpay.intake.review`) y `netpay_intake_connector_admin` (`read`, `netpay.intake.connect`), sin asignación efectiva a ninguna persona. La eventual excepción bootstrap queda suspendida hasta que se resuelva un Principal canónico inequívoco, se compruebe su membresía activa en Distribución Netpay y la autoridad canónica competente apruebe la asignación. No se inventarán UUID, `external_subject`, membresía ni rol. Si llega a aprobarse, dura como máximo 30 días desde la autorización del primer piloto real, exige revisión obligatoria al día 14 y se revoca al vencer, ante compromiso de cuenta, cambio de control del buzón o incorporación de un segundo reviewer. No se amplía ningún rol existente de Netpay automáticamente. Toda acción humana exige Principal, membresía activa, organización activa y permisos persistidos resueltos por `AuthorityResolutionService`. |
| 6. URI e identidad de credencial | El futuro proyecto Google dedicado se llamará `yarvis-netpay-intake` y estará bajo una identidad empresarial controlada por el propietario. El futuro cliente OAuth será de tipo **Desktop/local** y estará limitado a loopback local; la URI/callback concreta se determinará conforme al flujo permitido por ese tipo de cliente. Este borrador no crea proyecto, client ID, secreto ni credencial. Una futura configuración persiste únicamente `credential_secret_ref` opaco y la identidad segura del buzón; ningún token, secreto de cliente o autorización real se incluye en este paquete, repositorio, logs, eventos o navegador. |
| 7. Idempotencia | Entrega de proveedor: unicidad `(organization_id, connector_id, gmail_message_id)` y validación de huella inmutable; `gmail_thread_id` es sólo correlación. Comandos humanos: recibo por organización + contrato + `Idempotency-Key` + huella funcional; se revalida autoridad antes de consultar/repetir recibos, repetición idéntica devuelve el mismo resultado y cambio de payload devuelve conflicto. Cursor sólo avanza tras commit durable del lote. |
| 8. Confirmación humana | Revisión y descarte son actos explícitos de un `netpay_intake_reviewer`; ningún extractor, regla o futuro modelo acepta un candidato ni crea un caso. `AcceptNetpayIntakeCandidate` queda íntegramente diferido a MVP-2D2, fuera de esta ratificación y de cualquier mandato de esta variante. |
| 9. Exclusiones operativas | Sin OAuth real, consentimiento real, secreto, token, credencial, proyecto/cliente/recurso Google, buzón conectado, acceso al buzón, Pub/Sub, webhook, `watch`, polling, scheduler, worker, cola, broker, sincronización, migraciones, código, descarga de bytes, OCR, IA, storage, Document Registry, portal, WhatsApp, migración/backfill legacy, creación automática de casos ni acciones externas. |

El uso de `gmail.readonly` es el único scope que podría solicitar una futura
implementación; no queda solicitado ni concedido por este documento.

## 4. Autoridad y contratos propuestos para la variante, sin alterar el catálogo canónico

Esta tabla solicita que una futura enmienda ratificada asigne las identidades
siguientes exclusivamente para MVP-2D1 Manual Review Variant. Hasta que el
catálogo canónico se actualice mediante su propio procedimiento, son reservas
semánticas propuestas y no contratos ejecutables.

| ID propuesto | Nombre | Decisión de alcance |
| --- | --- | --- |
| `IC-NETPAY-CMD-016` | `ConfigureNetpayGmailConnector` | Admin humano configura, pausa o desconecta el enlace explícito. La variante no ejecuta OAuth real ni persiste secretos. |
| `IC-NETPAY-CMD-017` | `SynchronizeNetpayGmailConnector` | Propuesta contractual para una futura solicitud manual de sincronización. Hasta que el catálogo canónico la registre y un gate independiente la habilite, no está registrada ni es despachable: toda invocación se rechaza como `gate_closed`, no accede a Gmail, no crea candidatos, no mueve cursor y no produce efectos externos ni persistentes. La ratificación del diseño no constituye autorización de ejecución. |
| `IC-NETPAY-CMD-018` | `ReviewNetpayIntakeCandidate` | Revisión humana: corregir sugerencias o disponer `needs_review`, `dismissed`, `duplicate` o `failed`; sin mutar caso. |
| `IC-NETPAY-QRY-007` | `ListNetpayIntakeCandidates` | Consulta tenant-scoped propuesta de candidatos y salud segura del conector. La salud futura usa sólo la allowlist cerrada definida abajo. |
| `IC-NETPAY-QRY-008` | `RetrieveNetpayIntakeCandidate` | Consulta tenant-scoped de detalle seguro, procedencia y disposición. |
| `IC-NETPAY-EVT-007` | `NetpayIntakeCandidateReceived` | IDs seguros, conector, organización, estado y trazas; sin contenido, direcciones ni credenciales. |
| `IC-NETPAY-EVT-008` | `NetpayIntakeCandidateReviewed` | Disposición, actor, código de razón y trazas seguras. |
| `IC-NETPAY-EVT-010` | `NetpayGmailConnectorSyncFailed` | ID de conector y categoría segura; nunca payload del proveedor o detalle de credenciales. |

`IC-NETPAY-CMD-019` y `IC-NETPAY-EVT-009` quedan íntegramente diferidos a
MVP-2D2. No son contratos propuestos, asignados ni reservados por
MVP-2D1 Manual Review Variant.

La allowlist cerrada de toda futura respuesta o registro de salud es:
`mailbox_configuration_id`, `organization_id`, `status` (enum),
`last_attempt_at`, `last_success_at`, `candidate_count` agregado, `error_code`
controlado y `cursor_present` (booleano). `error_code` sólo puede pertenecer a
un catálogo controlado. Se prohíbe incluir remitentes, destinatarios,
direcciones de correo, asuntos, cuerpos, snippets, message IDs, header values,
nombres de adjuntos, tokens, label names, texto libre proveniente de Gmail,
excepciones o respuestas crudas del proveedor.

El ejecutor técnico futuro estará sujeto a una configuración persistida de un
solo conector y organización. No representa a un humano, no puede revisar,
aceptar, invocar CMD-009, mutar Master ni cruzar organizaciones. Su existencia
en runtime requiere autorización posterior; este documento no crea la
identidad ni el mecanismo de credenciales.

## 5. Criterios de aceptación para un futuro mandato de la variante

El mandato de implementación deberá exigir, como mínimo, evidencia reproducible
con proveedor falso y sin correo comercial real de que:

1. sólo un admin autorizado configura el enlace explícito y un vínculo
   ambiguo/ajeno queda oculto o rechazado sin mutación;
2. un disparo manual usa exclusivamente `gmail.readonly`, el filtro y el
   límite de 30 días, sin scheduler ni ejecución diferida, y sólo después de
   verificar el `label_id` persistido del mailbox binding;
3. mensajes repetidos no duplican candidatos, eventos ni avance de cursor; una
   huella conflictiva queda en cuarentena/fallo seguro;
4. fallo de lote, cursor inválido o revocación preserva el último cursor válido,
   falla cerrado y no crea/modifica casos ni Master;
5. contenido HTML/MIME hostil no se ejecuta ni aparece en logs/eventos, se
   aplican el límite de extracto y las reglas de retención, y el eventual
   expurgo demuestra eliminación efectiva e idempotente con tombstone/hash,
   timestamps y constancia auditable, incluido legal hold explícitamente
   autorizado, vencimiento del hold y `retention_blocked` fail-closed ante fallo;
6. lectura, revisión, ocultamiento cross-tenant, revalidación de autoridad e
   idempotencia de mandatos humanos se prueban de forma focalizada;
7. no aparecen secretos, tokens, bytes de adjuntos, Pub/Sub, polling, workers
   ni rutas de mutación automática; y
8. cualquier migración futura prueba upgrade, downgrade y re-upgrade, además de
   pruebas focalizadas, compilación y `git diff --check`; y
9. no se habilitan OAuth real, secretos, credenciales, recursos Google, acceso
   al buzón, migraciones, sincronización ni código antes del gate independiente
   aplicable.

## 6. Riesgos y rollback

| Riesgo | Control y rollback |
| --- | --- |
| Enlace a tenant erróneo | Selección explícita y unicidad de buzón; pausar/deshabilitar el conector conserva auditabilidad y evita nuevas lecturas. |
| Duplicado o cursor inconsistente | Dedupe por mensaje/conector/organización, cursor tras commit; deshabilitar el conector no modifica casos. |
| Exposición de PII o secreto | Extracto limitado, eventos seguros y referencia opaca; detener el conector y revocar/borrar una futura credencial conforme al procedimiento aprobado. |
| Automatización prematura | No hay scheduler, Pub/Sub ni `watch`; el rollback es deshabilitar el único disparo manual. |
| Confusión con legado o Radar | Prohibición de migrar, enlazar o backfillear legado y los 62 registros excluidos; el candidato sigue siendo evidencia separada. |

## 7. Discrepancia documental y reconciliación requerida

`CURRENT_STATE` y `CURRENT_SPRINT` mantienen como gate activo F-011/Radar y
declaran el Radar como paquete activo. `F011_STAGE_I_ACCEPTANCE.md` declara
F-011 COMPLETE/VALIDATED, mientras el historial de la rama,
`IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` (ratificado y con exclusión expresa
de Gmail/sincronización) y el diseño MVP-2D describen además el Inbox de
Netpay. Esta
discrepancia no concede autoridad por inferencia.

Antes de abrir un mandato de MVP-2D1 Manual Review Variant, el responsable de gobernanza debe emitir una
reconciliación documental separada que:

1. indique si MVP-2 Inbox es evidencia histórica aceptada, paquete activo o
   paquete suspendido respecto de F-011;
2. preserve que `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` está ratificado para
   contratos/autoridad Inbox y excluye expresamente Gmail/sincronización;
3. incluya expresamente `CURRENT_STATE`, `CURRENT_SPRINT`, roadmap, IG-006,
   F-011 Stage I, Radar y `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`; determine cuál fuente de estado
   prevalece y actualice coherentemente los registros sin alterar
   retrospectivamente la autoridad de IG-006; y
4. enumere el identificador secuencial de la enmienda Gmail, tras comprobar que
   no colisiona con enmiendas existentes.

## 8. Punto exacto de autorización futura

Ningún código queda autorizado al ratificar este borrador. La implementación de
MVP-2D1 Manual Review Variant quedará autorizada sólo cuando concurran **todos**
los hechos siguientes:

1. la Architecture Authority ratifica una enmienda independiente basada en
   este borrador, con el buzón, etiqueta y propietario empresarial del proyecto
   aprobados; dicha ratificación no crea todavía cliente OAuth, secreto ni
   credencial;
2. el catálogo canónico asigna formalmente sólo los IDs de la variante
   (`CMD-016..018`, `QRY-007..008`, `EVT-007..008` y `EVT-010`) y excluye
   expresamente `CMD-019` y `EVT-009` hasta MVP-2D2;
3. se publica la reconciliación obligatoria indicada en la sección 7, antes de
   emitir el gate de implementación;
4. se emite un gate/mandato de implementación explícitamente aprobado que
   nombre la rama, el SHA base corregido, alcance de la variante, contratos habilitados,
   entorno permitido y criterios de aceptación de la sección 5; y
5. la revisión de seguridad/privacidad aprueba el mecanismo real de
   credenciales antes de cualquier consentimiento OAuth o conexión externa.

La ausencia de cualquiera de esos hechos conserva MVP-2D1 Manual Review Variant como diseño y no
autoriza implementación, OAuth, sincronización ni contacto con Gmail.

## Registro de aprobación requerido

Quedan registradas las decisiones humanas de buzón, etiqueta exclusiva,
backfill de 30 días, retención de 90 días, extracto de 4 KiB, futuro proyecto
dedicado, cliente Desktop/local, bootstrap propuesto bajo condición suspensiva y
diferimiento completo de CMD-019/EVT-009 a MVP-2D2. La aprobación final aún
debe ratificar este paquete, resolver canónicamente Principal/membresía antes de
cualquier bootstrap, designar formalmente la identidad empresarial propietaria
y verificar el mecanismo loopback admitido antes de crear cualquier cliente.
