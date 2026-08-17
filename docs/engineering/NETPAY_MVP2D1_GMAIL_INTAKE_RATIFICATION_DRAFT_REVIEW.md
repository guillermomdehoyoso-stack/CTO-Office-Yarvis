# Revisión adversarial — Netpay MVP-2D1 Gmail Intake ratification draft

## Estado, alcance y decisión

**REVISIÓN INDEPENDIENTE — EL BORRADOR NO PUEDE RATIFICARSE TODAVÍA. REQUIERE
ENMIENDA.**

Se revisó exclusivamente
`NETPAY_MVP2D1_GMAIL_INTAKE_RATIFICATION_DRAFT.md`, su cadena documental y la
evidencia local de autoridad. Esta revisión no modifica contratos canónicos,
catálogo, código, `authentication.py`, configuraciones ni datos.

La ratificación documental propuesta **no autoriza** OAuth, consentimiento,
secretos, credenciales, proyecto o cliente Google, recursos Google, acceso al
buzón, lectura de mensajes ni sincronización real. La identidad empresarial
propietaria del proyecto Google, el mecanismo/almacenamiento de credenciales y
la comprobación final del flujo loopback son condiciones de un gate futuro de
implementación; no constituyen autoridad por estar mencionadas en el borrador.

## Dictamen

**No ratificable hasta corregir los BLOCKER B-001 y B-002.** Después, deberá
revisarse que la reconciliación documental requerida resuelva las observaciones
de gobernanza antes de abrir cualquier gate de implementación. Esta revisión no
recomienda crear recursos ni acceder a Gmail.

## Hallazgos

| ID | Clasificación | Hallazgo y evidencia | Corrección requerida |
| --- | --- | --- | --- |
| B-001 | **BLOCKER** | El borrador se llama y se autodefine como “MVP-2D1 manual”, pero no denomina explícitamente la variante **“MVP-2D1 Manual Review Variant”** ni declara que sustituye, únicamente para este alcance Netpay/Gmail, la definición D1 de `NETPAY_MVP2D_GMAIL_INTAKE_DESIGN.md`. El D1 original incluye OAuth/configuración y no UI de revisión; por tanto, coexistirían dos D1 incompatibles. | Renombrar el alcance dentro del borrador como **MVP-2D1 Manual Review Variant** y añadir una cláusula de sustitución limitada: reemplaza sólo el D1 de MVP-2D0 para Gmail Intake Netpay; no modifica D2–D5, Amendment 012, F-011, catálogo ni otros dominios. Expresar qué elementos D1 originales quedan sustituidos y cuáles se difieren. |
| B-002 | **BLOCKER** | No se pudo identificar inequívocamente el `Principal` canónico de Guillermo. Las referencias encontradas son nombres narrativos (`Guillermo`/`Guillermo de Hoyos`) y el Radar usa el texto `owner="Guillermo"`; no se localizó un `principal_id`, `external_subject` ni una membresía activa verificable para `59650e6f-ad62-40c3-8cb0-7710a122ce8b`. `local_netpay_authority.py` crea/resuelve Principal por `external_subject`, lo que confirma que el nombre no es identidad canónica. | No inventar identificadores. Antes de ratificar, obtener evidencia de sólo lectura de la fuente canónica que relacione el Principal, su `external_subject`, membresía activa, organización y roles, y registrar el identificador confirmado o retirar la asignación nominal de bootstrap del borrador. |
| M-001 | **MAJOR** | La sección de contratos se titula “contratos propuestos” y su tabla enumera CMD-019/EVT-009, aunque sus filas dicen que no se ratifican ni reservan. La cabecera puede interpretarse como propuesta de asignación de ambos, contraria al diferimiento íntegro exigido. | Separar CMD-019 y EVT-009 en una sección “Fuera de MVP-2D1 / no propuestos ni reservados” y limitar la tabla de asignación D1 a CMD-016..018, QRY-007..008 y EVT-007..008/010. |
| M-002 | **MAJOR** | La excepción temporal de bootstrap concede tres roles a Guillermo, pero no establece duración, autoridad que la aprueba, condición de expiración/revocación, ni evidencia de la membresía canónica. Aun después de resolver B-002, una excepción sin terminación resulta ampliable por inferencia. | Definir dueño de la excepción, condición objetiva de expiración o revisión, mecanismo de revocación y registro de auditoría; aplicarla sólo al Principal confirmado y a la organización indicada. |
| M-003 | **MAJOR** | “Retención 90 días” coexiste con “no se implementa expurgo físico automatizado”. Sin distinguir plazo de visibilidad de plazo de conservación física, el texto puede prometer una eliminación que D1 no está autorizado a ejecutar. | Definir 90 días como política de disponibilidad/retención objetivo y declarar expresamente que borrado, expurgo, legal hold y automatización de retención quedan fuera de D1 y requieren mandato posterior. |
| M-004 | **MAJOR** | La etiqueta se fija por nombre visible `Yarvis/Netpay-Intake`, pero Gmail opera técnicamente con identificadores de etiqueta. El nombre no debe convertirse en selector de tenant ni asumirse estable. | Mantener el nombre como decisión de producto, pero exigir que una futura configuración resuelva y persista el `label_id` asociado tras validación explícita del administrador; si falta o es ambiguo, no sincronizar. |
| M-005 | **MAJOR** | La reconciliación reconoce la contradicción F-011/Radar vs. Inbox/Amendment 012, pero omite evidencia adicional: `F011_STAGE_I_ACCEPTANCE.md` declara F-011 COMPLETE/VALIDATED en base `78eb6b3…`, mientras `CURRENT_STATE`/`CURRENT_SPRINT` aún lo declaran In Progress y limitan el paquete al Radar. Esto impide determinar el gate vigente sólo desde los documentos actuales. | La reconciliación debe identificar la fuente de estado que prevalece, incluir Stage I, actualizar Estado/Sprint/roadmap con el baseline y gate reales, y confirmar que Amendment 012 permanece ratificada pero no autorizadora de Gmail. |
| MIN-001 | **MINOR** | La frase “consulta obligatoria” mezcla el nombre de etiqueta con sintaxis de búsqueda. La futura implementación debe usar el mecanismo Gmail compatible con el tipo de cliente/proveedor, sin transformar esa consulta en autorización o inferencia de organización. | Describirla como política de selección y dejar el detalle de API (`label_id`/query) al diseño de implementación y sus pruebas con proveedor falso. |
| MIN-002 | **MINOR** | El documento habla de “salud segura del conector” y de un ejecutor técnico futuro sin especificar la categoría de fallo visible ni su frontera de datos. | Vincular esa superficie sólo a `EVT-010` y a categorías seguras; prohibir direcciones, asunto, cuerpo, identificadores de token y detalles de proveedor. |
| EDIT-001 | **EDITORIAL** | Se alternan “Amendment 012” y terminología inglesa/española sin una forma normativa consistente. | Usar “Implementation Roadmap Amendment 012” en la primera referencia y una abreviatura definida después. |
| OBS-001 | **OBSERVATION** | SHA `50cbb26e1828a711382cb35818b722eb69a04ce2` y Alembic `20260814_39` están registrados correctamente; se corrige la variante de SHA inexistente. | Ninguna. |
| OBS-002 | **OBSERVATION** | El borrador excluye expresamente OAuth real, secretos, credenciales, Pub/Sub, scheduler, acceso al buzón y mutaciones automáticas. También mantiene `CMD-019` y `EVT-009` fuera de ejecución D1. | Conservar estas exclusiones tras la enmienda; M-001 exige hacer el diferimiento inequívoco también en la estructura de contratos. |

## Autoridad e identidad: resultado de la inspección de sólo lectura

La evidencia local confirma el modelo canónico `Principal` y
`PrincipalMembership`, y la regla de que los permisos se derivan de datos
persistidos mediante `AuthorityResolutionService`. No se encontró una fuente de
datos versionada ni un registro canónico que pruebe cuál Principal corresponde
a Guillermo, ni que pruebe su membresía activa en Distribución Netpay. Los
documentos que lo nombran como Architecture Authority no sustituyen esa prueba.

Por ello B-002 es BLOCKER: el correo, el nombre humano, headers y valores de
Radar no son identificadores de autoridad. La revisión no propone UUID,
`external_subject` ni rol alguno.

## Evaluación de reconciliación y gate futuro

La reconciliación es necesaria y debe ocurrir antes de un gate D1. Debe abarcar
al menos `CURRENT_STATE`, `CURRENT_SPRINT`, roadmap aplicable, IG-006,
`F011_STAGE_I_ACCEPTANCE.md`, Radar y Amendment 012. La constatación mínima es:

```text
Amendment 012: contratos Inbox ratificados; Gmail no autorizado.
F-011 Stage I: evidencia de cierre declarada.
CURRENT_STATE / CURRENT_SPRINT: todavía describen F-011 en progreso y Radar
como único paquete activo.
```

La reconciliación no puede inferir que D1 está abierto. Debe nombrar el gate
independiente, los contratos D1 formalmente asignados y las condiciones de
seguridad antes de habilitar cualquier implementación.

## Condiciones para una nueva revisión

La versión enmendada podrá volver a revisión cuando:

1. adopte literalmente el nombre **MVP-2D1 Manual Review Variant** y la
   sustitución acotada indicada en B-001;
2. resuelva B-002 con evidencia canónica o elimine la concesión nominal de
   bootstrap;
3. retire CMD-019/EVT-009 de toda lista de asignación/reserva D1;
4. precise las condiciones de bootstrap, retención, etiqueta y reconciliación;
   y
5. conserve que propietario empresarial Google, credential store y validación
   loopback son precondiciones de un gate futuro, no efectos de la ratificación.

La aprobación posterior de este documento o de su borrador enmendado seguirá
sin autorizar OAuth, secretos, credenciales, recursos Google ni acceso real al
buzón hasta que el gate independiente sea emitido y satisfecho.
