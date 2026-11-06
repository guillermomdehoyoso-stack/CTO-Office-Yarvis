# Amendment 032 — IG-016A C4 resultados operativos y efecto financiero

**RATIFIED — C4 LOCAL SYNTHETIC IMPLEMENTATION AND VALIDATION ONLY**

Fecha: 2026-11-05

Base verificada: `70c6f9397c0ec772ec19c3f5d84f7a61c4024a4c`

Ratificación: 2026-11-06. La autoridad aprobó los borradores identificados por:

- Amendment 032 SHA-256
  `B5EDF8C6710DA432396986EC5B426F3840756C936947B90117548F80998A60D8`;
- IG-016A C4 SHA-256
  `97C9BDC4EE57C3CCBEBE0273D67BC1EC2579DD1C01DF4DF71CFD40EF42F1FF29`.

La ratificación autoriza únicamente implementación y validación local sintética,
migración 59 y registro de CMD-049/050 y QRY-030. Mantiene todas las exclusiones
de §7 y no autoriza EVT ni contratos adicionales.

Diseño subordinado propuesto:
[IG-016A C4](IG-016A_C4_VERIFIED_OUTCOMES_AND_FINANCIAL_EFFECTS.md)

## 1. Decisión solicitada

Se propone una autorización independiente y limitada para diseñar e implementar
localmente C4 de IG-016A con datos exclusivamente sintéticos. C4 registra
evidencia posterior, verifica resultados operativos y produce evaluaciones
financieras trazables sin convertir compromisos humanos en resultados ni
proyecciones en dinero recuperado.

Esta ratificación abre sólo C4 local sintético con los contratos, migración y
pruebas expresamente definidos. C1–C3 permanecen cerrados como PASS publicados.

## 2. Alcance canónico

Amendment 029 e IG-016 asignan a C4 la reactivación verificada, la devolución de
equipo verificada y la validación financiera posterior. Amendment 030 conserva
outcomes/snapshots en C4. Amendment 031 termina C3 en decisión y seguimiento:
`reactivation_agreed` y `return_requested` son compromisos, no resultados.

C4 agrega sólo:

- evidencia operativa posterior, inmutable y con procedencia;
- evaluación versionada de reactivación o recuperación física;
- snapshots financieros reproducibles con componentes disjuntos y certeza;
- cierre de caso con versión esperada y brechas explícitas;
- consulta minimizada de outcome y efecto financiero.

C4 no importa fuentes reales, no confirma caja, no crea un ledger y no altera
Master, identidad de equipo, condiciones comerciales ni evidencia C1/C2.

La implementación local usaría sólo los perfiles cerrados
`synthetic_c4_activity_v1`, `synthetic_c4_return_inventory_v1` y
`synthetic_c4_financial_effect_v1`. Cada perfil exige procedencia
`synthetic_fixture`, IDs sintéticos, tiempos con zona y ventanas válidas; rechaza
hashes, batches, links o referencias de las fuentes reales. Elegir perfiles y
autoridades reales permanece pendiente para un piloto posterior.

## 3. Discrepancia contractual y resolución propuesta

IG-016 reservaba conceptualmente CMD-049/050 para evidencia y cierre, y usaba
QRY-028/029 para métricas y cobertura. El primer borrador IG-016A proponía
CMD-046 `VerifyNoUsageRecoveryOutcome` y EVT-033 para C4. C3 registró CMD-046
como `AssignAndPlanProtectionCase` y QRY-028/029 con semánticas de cola y
detalle; ninguno puede redefinirse. La propuesta C4 adopta los CMD-049/050 de la
autoridad superior y desplaza la lectura de outcome a QRY-030. Los tres IDs
están libres en la base verificada, pero este documento no los registra ni
reserva. La antigua propuesta EVT-033 queda desplazada y no registrada.

No se propone EVT. EVT-031+ continúan libres porque no existe consumidor real
demostrado; historial y snapshots append-only bastan para validación local. Un
evento futuro requerirá consumidor, payload y autoridad separados.

## 4. Contratos candidatos

| ID libre verificado | Nombre candidato | Semántica mínima | Permisos resueltos por servidor |
| --- | --- | --- | --- |
| `IC-NETPAY-CMD-049` | `RecordProtectionOutcomeEvidence` | añadir evidencia y evaluación operativa posterior sin cerrar el caso | `netpay.inbox.manage` + `netpay.portfolio.reconciliation.read` |
| `IC-NETPAY-CMD-050` | `CloseProfitabilityProtectionCase` | cerrar o cerrar con brecha usando versión y outcome vigente | `netpay.inbox.manage` + `netpay.portfolio.reconciliation.read` |
| `IC-NETPAY-QRY-030` | `RetrieveProtectionOutcomeAssessment` | leer outcome, procedencia, brechas y snapshot financiero minimizado | `netpay.portfolio.read`; detalle de evidencia exige `netpay.portfolio.reconciliation.read` |

No se acepta rol, permiso o grant declarado por el cliente. El runtime usa el
`IdentityAuthorityEnvelope` resuelto por el servidor. No se crean roles,
capabilities, grants ni cambios OIDC.

## 5. Persistencia candidata

Alembic tiene un solo head `20261102_58`. El identificador libre propuesto es
`20261105_59_netpay_protection_outcomes.py`, descendiente directo de 58. No se
crea ni reserva mediante este borrador.

La revisión podría agregar outcomes, referencias de evidencia, evaluaciones y
snapshots financieros append-only/superseding. Excluye bytes fuente, contacto,
PII, ledger, cuenta bancaria, importadores reales y tablas de mensajes.

La revisión vigente se deriva de la cadena `supersedes_id`: es la única hoja sin
sucesor de una raíz. No existe bandera mutable `current`. UPDATE/DELETE de
evidencia, evaluación y snapshot se rechazan; una corrección agrega una revisión
y conserva la anterior. Si corrige evidencia usada por un cierre, el cierre
histórico permanece y su evaluación pasa a `stale` de forma derivada. Sólo un
actor con permisos C4 resueltos por servidor puede registrar la corrección, y un
sucesor de caso se abre mediante el CMD-045 vigente con referencia explícita al
caso terminal; el caso cerrado nunca se reabre in-place.

## 6. Gate local propuesto

La implementación autorizable sería exclusivamente local y sintética:

- PostgreSQL desechable, sin puertos publicados y sin datos operativos;
- migración 58→59→58→59 y head único;
- contratos candidatos registrados sólo después de ratificación;
- fixtures sintéticos con perfiles temporales cerrados;
- matriz exhaustiva de `closure_kind` y errores deterministas;
- fórmulas Decimal, redondeo, atribución y doble conteo reproducibles;
- pruebas de evidencia, estados, certeza, supersesión, idempotencia,
  concurrencia, permisos, aislamiento y minimización;
- regresión C1–C3, IG-015 e IG-016 A/B.

PASS exige todos los criterios del diseño subordinado. FAIL incluye cualquier
inferencia de resultado o dinero, doble conteo, PII, mutación de evidencia o
last-write-wins. BLOCKED aplica cuando falta autoridad de fuente, regla de
comparabilidad o significado financiero necesario para el fixture evaluado.

## 7. Exclusiones

Fuentes o links reales; importación; contacto; mensajería; frontend; piloto;
producción; despliegue; migración productiva; caja o depósito bancario; ledger;
reprocesamiento; exportación; OIDC; roles; grants; capabilities; EVT; contratos
adicionales; staging; commit y push.

## 8. Condiciones para un piloto posterior

Sin crear otra fase C por defecto, un piloto requeriría como mínimo: perfiles y
autoridad de las fuentes reales; temporalidad vigente de identidad; catálogo
aprobado de conceptos comparables; fuente autorizada de recepción/inventario;
reglas financieras y ventanas aprobadas; permisos operativos comprobados;
checkpoint humano; rollback; observabilidad segura; UAT; y autorización separada
de importación, interfaz, migración y despliegue.

## 9. Efecto de ratificación

Esta ratificación abre sólo implementación local sintética C4, migración 59,
CMD-049/050 y QRY-030, conservando todas las exclusiones de §7. Un PASS técnico
no autoriza fuente real, piloto, producción, staging, commit o push.

## 10. Resultado local

C4 quedó **PASS local sintético** el 2026-11-06. La revisión `20261105_59`
desciende directamente de 58; el ciclo 58→59→58→59 y el head único pasaron en
PostgreSQL tmpfs sin puertos. Se registraron sólo CMD-049/050 y QRY-030. La suite
C4 final pasó 14 pruebas y la regresión consolidada pasó 110 pruebas. Ruff,
compilación y las garantías append-only pasaron. Evidencia:
[IG-016A C4 local](evidence/netpay-ig016a-c4-local-20261106.txt).

Este PASS no abre ninguna exclusión de §7.
