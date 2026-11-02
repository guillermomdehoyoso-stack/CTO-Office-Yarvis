# Amendment 030 — IG-016A No Uso, identidad de equipos y recuperación

**RATIFIED — C1 LOCAL IMPLEMENTATION AND VALIDATION ONLY**

Fecha: 2026-11-01

Base documental: `c43361a491db9a8c0d4f8b3d190dd2faef4d0a15`

Diseño subordinado propuesto:
[IG-016A](IG-016A_NETPAY_NO_USAGE_EQUIPMENT_RECOVERY_AUTHORIZATION.md)

Perfiles y contratos propuestos:
[revisión 2026-11-01](NETPAY_IG016A_SOURCE_PROFILE_AND_CONTRACT_REVIEW_20261101.md)

## 1. Decisión solicitada

Se propone subdividir el Gate C de IG-016 en cuatro autorizaciones independientes
para llevar fuentes reales de No Uso y equipo desde preview controlado hasta una
recuperación verificada. La ratificación del 2026-11-01 abre únicamente C1; C2–C4 permanecen cerrados.

La primera decisión recomendada es autorizar únicamente **C1 — perfiles y
preview**, sin persistencia operativa, migración, contacto ni aceptación real.
C2–C4 requerirían ratificaciones posteriores con evidencia propia.

## 2. Autoridad y propiedad

Netpay Merchant Operations conserva la identidad operativa Store–equipo, los
casos y sus decisiones. Operational Data conserva lotes, filas observadas y
procedencia. Master conserva Client, Company, Branch y contacto. Operational
Economics conserva hechos económicos genéricos. IG-016A puede proyectar
penalizaciones Netpay con procedencia, pero no crea un ledger ni confirma caja.

Store exacto es la única clave comercial autorizada. Terminal, serie, MID y TID
son espacios distintos. Estas fuentes no contienen MID/TID explícito. Nombre,
domicilio, contacto y similitud no resuelven identidad.

## 3. Decisión temporal

Los 20 vínculos de Gate G son exactos y evidenciados para los lotes observados,
pero no demuestran asignación vigente. Hasta contar con corte o vigencia se
representan como `resolution_status = pending` y razón
`pending_temporality`. No se crea un estado `confirmed` ni un caso contactable
por esos vínculos durante C1/C2.

Los 12 Stores de No Uso ausentes de ambos Globales quedan
`missing_equipment_match`. Los 18 equipos sin Store ni cliente quedan
`missing_store_and_client`. Ninguno se asigna o completa automáticamente.

## 4. Fuentes independientes

La propuesta define tres perfiles incompatibles entre sí:

| Perfil candidato | Fuente identificada en Gate G | Uso permitido |
| --- | --- | --- |
| `netpay_no_usage_oct26_v1` | SHA-256 `2f93cb0589219642c129c764ce29328974400a1a942b068f7b09b466e1899d0c` | filas de campaña por Store; sin equipo ni corte confirmado |
| `netpay_global_equipment_oct26_v1` | SHA-256 `58bb41ec0d273122820822362953565e3aa82c092b75b5377c98c7c06f49c6d7` | observación Store–terminal–serie sin cliente |
| `netpay_ticket97580_equipment_client_oct26_v1` | SHA-256 `b22849379cfa03a70edda41744ae0956a5667ccbb8e92b596fcf4e5a84f896da` | enriquecimiento Client/Company/Branch y presencia de contacto |

El hash identifica el lote, no el perfil general. Un archivo corregido recibe
nuevo hash y nuevo lote. Una firma estructural distinta se rechaza como perfil
incompatible; no se elige por ser más reciente ni se sustituye otro lote.

## 5. Valores especiales

- `NA` se clasifica `placeholder` y nunca crea identidad.
- `#N/A` se clasifica `cell_error` y nunca es valor de negocio.
- vacío se clasifica `blank`; no es cero.
- fila numerada sin Store se clasifica `template_row`.
- Store ausente se conserva como `missing_store`.
- equipo o cliente ausente se conserva como `missing_equipment` o
  `missing_client`.
- un valor fuera del perfil se clasifica `unsupported_value`.

La aceptación futura conservaría original y normalizado para identificadores no
PII. PII de Ticket no se copia a filas operativas: se resuelve contra Master o
se conserva como referencia de evidencia restringida.

## 6. Pipeline propuesto

```text
registro de fuente
  -> SHA-256
  -> firma estructural
  -> preview efímero
  -> clasificación / normalización no destructiva
  -> correspondencia exacta
  -> exactos / pendientes / ambiguos / contradictorios / excluidos
  -> checkpoint humano
  -> aceptación idempotente
  -> persistencia tenant-scoped
  -> casos de recuperación
  -> readback
  -> evidencia y auditoría
```

Preview no implica aceptación. Aceptación no implica activar casos o contacto.
Activación operativa requiere C3 y una decisión humana por caso.

## 7. Subgates

| Subgate | Alcance | Persistencia | Estado propuesto |
| --- | --- | --- | --- |
| C1 | perfiles, parsers, firmas, preview y clasificación | ninguna | primera ratificación recomendada |
| C2 | checkpoint, aceptación, evidencia, identidad pendiente y readback | local/aislada tras ratificación | cerrado |
| C3 | contacto protegido, casos, asignación, estados y acciones | casos/historial | cerrado |
| C4 | reactivación, devolución y resultado financiero verificable | outcomes/snapshots | cerrado |

Cada subgate exige PASS/FAIL/BLOCKED y rollback propios. El PASS de uno no abre
el siguiente.

## 8. Contratos mínimos candidatos

Los registros runtime llegan a CMD-042, QRY-024 y EVT-030. Se proponen, sin
registro ni reserva, sólo:

- CMD-043..046: aceptar lote; abrir/actualizar caso; registrar acción; verificar
  outcome.
- QRY-025..027: preview; resultados/excepciones; cola/detalle.
- EVT-031..033: lote aceptado; caso cambiado; outcome verificado.

El preview es una query efímera y no emite evento. Los eventos contienen IDs,
estado y traza segura, nunca contacto, Client ID externo, notas o importes no
minimizados. Los IDs restantes de los rangos amplios de Amendment 029 no se
reservan.

## 9. Seguridad

Se reutilizan capacidades actuales antes de crear otras:

- `netpay.inbox.read/manage` para fuentes y mutaciones operativas;
- `netpay.portfolio.read` para cola minimizada;
- `netpay.portfolio.sensitive.read` para contacto completo;
- `netpay.portfolio.reconciliation.read` para excepciones seguras.

La combinación necesaria para PII completa permanece exclusiva del rol vigente
`netpay_operations_operator`. No se propone rol, grant, OIDC ni capability nueva.
Si la implementación no puede demostrar esa conjunción sin ampliar autoridad,
C3 queda BLOCKED y requiere Governance separado.

## 10. Migración candidata

`20261031_57` está libre y sería descendiente directa de `20261030_56`. No se
crea por este borrador ni por C1. Antes de C2 debe decidirse si una sola revisión
abarca lotes/filas/casos/historial/outcomes o si el principio de subgates exige
revisiones separadas. Ninguna revisión incluirá tasas, spread o tendencias de
IG-016B/C ni duplicará PII canónica.

## 11. Límites

Quedan fuera: importación real, contacto automático, exportación masiva,
mensajería, creación de Store, inferencia por PII, confirmación bancaria,
reprocesamiento histórico, producción, despliegue, activación, OIDC, roles,
IG-016B/C y Gates D–I.

## 12. Efecto de ratificación

Este documento es una propuesta. Una ratificación debe nombrar expresamente el
subgate autorizado, allowlist de archivos, fuentes reales permitidas, migración
si aplica y pruebas. Ratificar C1 no autoriza C2–C4.
