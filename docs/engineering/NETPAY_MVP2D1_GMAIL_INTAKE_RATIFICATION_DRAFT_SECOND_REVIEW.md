# Segunda revisión adversarial — MVP-2D1 Manual Review Variant

## Decisión

**AMENDMENT REQUIRED.** El borrador contiene evidencia suficiente para preparar
una enmienda formal independiente, pero no debe ratificarse hasta corregir los
dos hallazgos MAJOR de esta revisión. No se identificaron BLOCKER nuevos.

Esta decisión distingue tres actos que permanecen separados:

1. **Ratificación de diseño y límites:** puede fijar la variante, sus
   invariantes, parámetros y exclusiones; no habilita runtime.
2. **Asignación canónica futura de contratos:** sólo el procedimiento del
   catálogo canónico puede asignar CMD-016..018, QRY-007..008 y EVT-007..008/010;
   el borrador no los asigna hoy.
3. **Gate independiente de implementación:** sólo después de la ratificación,
   catálogo, reconciliación y precondiciones de seguridad puede abrir código,
   migraciones o una operación real. Ningún acto anterior habilita Gmail.

## Verificación de correcciones de la primera revisión

| Hallazgo previo | Resultado | Evidencia en el borrador actual |
| --- | --- | --- |
| B-001 — nombre y sustitución D1 | **Corregido** | Denomina literalmente **MVP-2D1 Manual Review Variant** y sustituye sólo D1/MVP-2D0 para Gmail de Distribución Netpay; preserva otros buzones, tenants y D2–D5. |
| B-002 — Principal de Guillermo | **Corregido por eliminación de asignación nominal** | No asigna rol efectivo a Guillermo ni inventa ID. Bootstrap queda suspendido hasta Principal inequívoco, membresía activa y aprobación canónica. |
| M-001 — CMD-019/EVT-009 en tabla | **Corregido** | No están en ninguna tabla de asignación; se declaran únicamente diferidos a MVP-2D2. |
| M-002 — bootstrap sin límites | **Corregido** | Máximo 30 días desde el primer piloto real, revisión día 14 y revocación por vencimiento, compromiso, cambio de control o segundo reviewer. |
| M-003 — retención/expurgo ambiguo | **Parcial; MAJOR S2-001** | Define 90 días, tombstone/hash/timestamps/auditoría e idempotencia futura, pero omite legal hold y conducta fail-closed si el expurgo no puede completarse. |
| M-004 / MIN-001 — etiqueta | **Corregido** | Nombre humano exacto, `label_id` canónico, mailbox binding, verificación por sincronización y prohibición de seleccionar sólo por nombre visible. |
| M-005 — reconciliación | **Corregido** | La hace prerrequisito anterior al gate y enumera Estado, Sprint, roadmap, IG-006, F-011 Stage I, Radar y Amendment 012. |
| MIN-002 — superficie segura | **Parcial; MINOR S2-002** | EVT-010 limita fallo a categoría segura, pero QRY-007 conserva “salud segura” sin delimitar expresamente sus campos visibles. |
| EDIT-001 — nombre de Amendment 012 | **Pendiente; EDITORIAL S2-003** | El documento continúa alternando “Amendment 012” sin una forma normativa definida. |

## Hallazgos de segunda revisión

| ID | Clasificación | Hallazgo | Corrección requerida |
| --- | --- | --- | --- |
| S2-001 | **MAJOR** | La retención ordena conservar sólo tombstone, hash, timestamps y constancia de expurgo al día 90, pero no contempla legal hold, fallo de eliminación ni la conducta cuando no puede expurgarse. Esto puede imponer una eliminación incompatible con preservación legal/auditabilidad o dejar un resultado indeterminado. | Declarar que un legal hold/obligación de preservación suspende el expurgo con registro seguro; que un fallo de expurgo es fail-closed, no elimina el tombstone ni afirma eliminación; y que el gate futuro prueba estas ramas además de eliminación efectiva e idempotente. |
| S2-002 | **MAJOR** | Aunque las secciones de estado excluyen sincronización presente, CMD-017 se describe como “Disparo manual autorizado”. En una tabla de contratos futuros puede leerse como autorización actual, contrariando la regla de que ratificación documental no habilita acceso ni sincronización. | Sustituir esa frase por alcance potencial futuro, por ejemplo “disparo manual que sólo un gate independiente futuro podría habilitar”, y repetir que no hay sincronización ni acceso al buzón en la presente ratificación. |
| S2-003 | **MINOR** | La verificación de `label_id` exige comprobarlo en cada sincronización, pero no determina la respuesta ante ausencia, cambio o desajuste. | Exigir fallo cerrado: no leer, crear candidatos ni avanzar cursor si el `label_id` no coincide con el mailbox binding persistido. |
| S2-004 | **MINOR** | “Salud segura del conector” no enumera su frontera de datos para QRY-007. | Limitarla a ID de conector, estado, timestamps y categorías seguras, excluyendo dirección, asunto, cuerpo, IDs de proveedor y credenciales. |
| S2-005 | **EDITORIAL** | La primera referencia usa “Amendment 012” sin nombre normativo consistente. | Definir “Implementation Roadmap Amendment 012” en la primera mención y usar la abreviatura acordada después. |
| S2-006 | **OBSERVATION** | SHA `50cbb26e1828a711382cb35818b722eb69a04ce2`, Alembic `20260814_39`, backfill de 30 días y extracto máximo de 4 KiB están expresados de forma verificable. | Ninguna. |
| S2-007 | **OBSERVATION** | Principal/membresía, identidad empresarial, seguridad del credential store y verificación final loopback se tratan como precondiciones futuras, sin ID ni autoridad presente. | Conservar esta separación. |
| S2-008 | **OBSERVATION** | No hay frase que habilite OAuth real, secretos, credenciales, recursos Google, migraciones, expurgo, código o asignación de roles en el presente. La única ambigüedad de autorización detectada es S2-002 sobre sincronización. | Corregir S2-002. |

## Límites y semántica normativa comprobados

- **Mailbox binding:** el correo se enlaza explícitamente con Distribución
  Netpay; metadatos, headers, dominio, contenido y workspace no seleccionan
  tenant.
- **`label_id`:** el nombre visible es configuración humana; el selector futuro
  es `label_id` persistido y verificado. S2-003 exige completar la respuesta al
  desajuste.
- **Backfill:** máximo 30 días desde el primer disparo manual, sin alcanzar los
  62 registros históricos excluidos.
- **Contenido y retención:** extracto saneado máximo 4 KiB; cuerpo, extracto y
  metadatos no indispensables máximo 90 días; el expurgo sólo puede existir
  tras gate y debe ser efectivo, auditable e idempotente. S2-001 aún condiciona
  su ratificación normativa completa.
- **Bootstrap:** no efectivo, sujeto a Principal y membresía canónicos,
  aprobación competente y límites temporales/revocación definidos. No concede
  rol actual a ninguna persona.
- **CMD-019 / EVT-009:** no se asignan, reservan ni ratifican para la variante;
  aparecen sólo como diferidos íntegramente a MVP-2D2.

## Precondiciones futuras y ausencia de autoridad presente

El texto trata correctamente Principal/membresía, reconciliación documental,
identidad empresarial, seguridad de credenciales y loopback como precondiciones
futuras. La ratificación de diseño no crea un Principal, membresía, proyecto
Google, cliente OAuth, secreto, credencial, mailbox binding ni acceso al buzón.

La reconciliación obligatoria debe preceder el gate y resolver el conflicto
entre F-011 Stage I y los registros vigentes de Estado/Sprint, preservando el
hecho de que Amendment 012 ratifica Inbox pero no Gmail.

## Siguiente acción mínima permitida

Enmendar únicamente el borrador para resolver S2-001 y S2-002; se recomienda
resolver también S2-003 a S2-005 en la misma enmienda. Después, ejecutar una
tercera revisión documental. No procede asignar contratos en el catálogo,
emitir un gate, crear recursos Google, pedir OAuth ni implementar código.
