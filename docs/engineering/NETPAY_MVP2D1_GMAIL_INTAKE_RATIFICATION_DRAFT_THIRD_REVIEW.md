# Tercera revisión adversarial y de cierre — MVP-2D1 Manual Review Variant

## Decisión única

**RATIFIABLE.** El borrador cierra todos los hallazgos BLOCKER, MAJOR, MINOR y
EDITORIAL de las dos revisiones anteriores. Contiene evidencia suficiente para
preparar una enmienda formal independiente de ratificación. No contiene una
autorización presente de implementación o de acceso a Gmail.

Las precondiciones conocidas —Principal/membresía, reconciliación, identidad
empresarial, credential store, loopback y revisión de seguridad— no son
hallazgos abiertos: el borrador las conserva explícitamente como condiciones de
etapas futuras y no les atribuye autoridad actual.

## Matriz de cierre

| Hallazgo previo | Severidad previa | Corrección aplicada y evidencia textual | Estado |
| --- | --- | --- | --- |
| B-001 — variante D1 ambigua | BLOCKER | Nombre literal **MVP-2D1 Manual Review Variant**; §2 sustituye sólo D1/MVP-2D0 para Gmail/Distribución Netpay y preserva otros buzones, tenants y D2–D5. | **Closed** |
| B-002 — Principal de Guillermo no verificable | BLOCKER | §3.5 no asigna rol efectivo, no inventa UUID/`external_subject` y suspende bootstrap hasta Principal, membresía y aprobación canónicas. | **Closed** |
| M-001 — CMD-019/EVT-009 en asignación D1 | MAJOR | §4 no los incluye en la tabla; texto posterior dice que no son propuestos, asignados ni reservados y quedan diferidos íntegramente a MVP-2D2. | **Closed** |
| M-002 — bootstrap ilimitado | MAJOR | §3.5 fija máximo 30 días, revisión al día 14 y revocación por vencimiento, compromiso, cambio de control o segundo reviewer. | **Closed** |
| M-003 — retención/expurgo ambiguo | MAJOR | §3.4 fija 90 días, tombstone/hash/timestamps/auditoría y reserva hold/expurgo/recuperación para gate futuro. | **Closed** |
| M-004 / MIN-001 — nombre visible de etiqueta | MAJOR / MINOR | §3.2 exige `label_id` canónico, mailbox binding persistido y verificación en cada sincronización; prohíbe fallback por nombre visible. | **Closed** |
| M-005 — reconciliación incompleta | MAJOR | §7 la hace obligatoria antes del gate y enumera `CURRENT_STATE`, `CURRENT_SPRINT`, roadmap, IG-006, F-011 Stage I, Radar y `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`. | **Closed** |
| MIN-002 — frontera de salud insegura | MINOR | §4 define allowlist cerrada y prohíbe PII, contenido Gmail, IDs de mensaje, headers, adjuntos, tokens, excepciones y respuestas crudas. | **Closed** |
| EDIT-001 — nombre de Amendment 012 | EDITORIAL | Todas las referencias vigentes usan `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`, identificado como ratificado y excluyente de Gmail/sincronización. | **Closed** |
| S2-001 — legal hold y fallo de expurgo | MAJOR | §3.4 exige autoridad canónica y campos auditables para hold; vencimiento reaplica retención. Fallo entra en `retention_blocked`, sin extensión silenciosa, con remediación/evidencia/reautorización. | **Closed** |
| S2-002 — CMD-017 parecía ejecutable | MAJOR | §4 lo limita a propuesta futura: no registrado ni despachable; invocación `gate_closed`, sin Gmail, candidatos, cursor ni efectos persistentes/externos. | **Closed** |
| S2-003 — desajuste de `label_id` | MINOR | §3.2 bloquea fail-closed ante `label_id` ausente, inválido, ambiguo, eliminado o inconsistente: sin consulta, candidatos ni avance de cursor. | **Closed** |
| S2-004 — salud sin límite de datos | MINOR | §4 permite sólo `mailbox_configuration_id`, `organization_id`, estado, timestamps, conteo agregado, `error_code` controlado y booleano de cursor. | **Closed** |
| S2-005 — nomenclatura documental | EDITORIAL | Referencia normalizada en §§0, 2 y 7 a `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md`. | **Closed** |
| S2-006..008 — evidencia/base y separación de autoridad | OBSERVATION | SHA corregido, Alembic, backfill 30 días, extracto 4 KiB y separación de precondiciones permanecen explícitos. | **Closed** |

## Controles específicos comprobados

- **Alcance:** la variante es limitada a D1/MVP-2D0 para el buzón y tenant
  declarados; no modifica otros buzones, tenants o fases.
- **Identidad y bootstrap:** no existe Principal, membresía ni rol efectivo
  inventado; el bootstrap es condicional, temporal y revocable.
- **Contratos:** CMD-019/EVT-009 están exclusivamente diferidos a MVP-2D2.
  CMD-017 no está registrado ni despachable y falla `gate_closed` hasta
  catálogo y gate futuros.
- **Intake:** mailbox binding explícito y `label_id` canónico fallan cerrado;
  no hay fallback por nombre ni avance de cursor/candidatos ante fallo.
- **Datos:** backfill máximo 30 días; extracto saneado máximo 4 KiB; retención
  ordinaria máxima 90 días.
- **Retención:** legal hold no está activo ni es creado por la ratificación;
  exige autoridad futura. `retention_blocked` impide sincronización/ingestión,
  cursor y candidatos hasta remediación auditable y reautorización humana.
- **Salud:** allowlist cerrada sin PII, contenido de Gmail, IDs de mensaje,
  headers, adjuntos, tokens ni respuestas/excepciones crudas del proveedor.
- **Gobernanza:** `IMPLEMENTATION_ROADMAP_AMENDMENT_012.md` se identifica como
  ratificado y excluyente de Gmail/sincronización; la reconciliación documental
  es un prerrequisito explícito.
- **Exclusiones presentes:** el borrador no autoriza OAuth, secretos,
  credenciales, recursos Google, Gmail real, migraciones, sincronización,
  expurgo, código ni asignación de roles.

## Separación de decisiones y gates

1. **Diseño ratificable:** el contenido de este borrador puede ratificarse como
   límites, invariantes y propuesta de alcance. La ratificación no ejecuta ni
   crea estado externo.
2. **Asignación canónica futura de contratos:** sigue pendiente del catálogo
   canónico; el borrador no registra los IDs hoy.
3. **Reconciliación documental:** debe resolver el estado F-011/Radar/Inbox y
   preceder al gate de implementación.
4. **Gate independiente de implementación:** sólo tras 1–3 puede autorizar el
   código, migraciones y el corte manual específicamente aprobado.
5. **Gate posterior de OAuth real:** aun con el gate de implementación, OAuth
   real, proyecto/cliente Google, credential store, identidad empresarial y
   loopback requieren la aprobación de seguridad/privacidad y el gate que
   habilite expresamente consentimiento o conexión externa. Nada en la
   ratificación presente habilita ese paso.

## Hallazgos abiertos

Ninguno. No se introducen requisitos nuevos: no se observó defecto concreto,
riesgo no controlado ni contradicción interna que justifique una enmienda
adicional antes de la ratificación documental.

## Siguiente acción mínima permitida

Preparar `docs/engineering/IMPLEMENTATION_ROADMAP_AMENDMENT_014.md` como la
enmienda formal independiente de ratificación para MVP-2D1 Manual
Review Variant, usando este borrador y sus tres revisiones como antecedentes.
Preparar esa enmienda no asigna contratos en el catálogo ni autoriza
implementación, OAuth, recursos Google, conexión al buzón, migraciones o código.
