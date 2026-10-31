# IG-016 — MVP de protección y recuperación de rentabilidad Netpay

**RATIFIED — GATES A AND B LOCAL IMPLEMENTATION AND SYNTHETIC TEST AUTHORITY ONLY**

Ratificado por instrucción explícita del usuario el 2026-10-30. Esta autoridad
no abre Gates C–I ni autoriza fuentes reales, importación, operación o
despliegue. El cierre técnico, commit y push de Gates A/B fueron autorizados
separadamente el 2026-10-31 sin abrir esos gates.

Fecha de propuesta: 2026-10-30

Roadmap propuesto: [Amendment 029](IMPLEMENTATION_ROADMAP_AMENDMENT_029.md)

Dependencias vigentes: IG-014 e IG-015 publicados

Fuentes y brechas: [revisión 2026-10-30](NETPAY_PROFITABILITY_PROTECTION_SOURCE_GAP_REVIEW_20261030.md)

## Estado ejecutado de Gates A/B — 2026-10-30

| Gate | Estado vigente | Evidencia |
| --- | --- | --- |
| A — Autoridad, inventario y fuentes | **PASS** | La autoridad se limitó a A/B, el grafo conserva un solo head `20261030_56`, no se registraron contratos públicos y `CMD-043+`, `QRY-025+` y `EVT-031+` siguen libres. |
| B — Identidad Store-terminal-serie | **PASS sintético — validación de fuentes reales pendiente en Gate G** | Servicio interno y persistencia tenant-scoped probaron multi-equipo, identidades sin Store, ambigüedad, contradicción temporal, aislamiento, replay, concurrencia, versión e historial. |

La ejecución usó sólo fixtures sintéticos y PostgreSQL local aislado. No
registró rutas, capabilities, roles, commands, queries ni eventos públicos. Gates
C–I permanecen cerrados. La evidencia reproducible está en
[`netpay-profitability-protection-ig016-ab-20261030.txt`](evidence/netpay-profitability-protection-ig016-ab-20261030.txt).

## 1. Objetivo y límites

Diseñar un sistema de atención que encuentre riesgo económico por Store, lo
vincule con identidad operativa comprobada, produzca una acción humana
responsable y mida después el resultado operativo y financiero. Esta propuesta
no es autoridad de implementación, importación, migración, publicación o piloto.

El lenguaje de negocio y toda interfaz nueva usan exclusivamente **Reporte
mensual de rentabilidad Netpay**. Los nombres técnicos de perfiles históricos no
se trasladan a etiquetas ni definiciones de negocio nuevas.

## 2. Modelo funcional y propiedad

| Concepto | Definición propuesta | Invariantes |
| --- | --- | --- |
| `ProfitabilityProtectionCase` | Alerta/expediente operativo por Organization y causa material | No reemplaza Master, Inbox ni Operational Task; conserva origen y versión |
| `StoreEquipmentObservation` | Observación de Store, terminal, MID y serie en una fuente/lote/periodo | Cada identidad es separada; ausencia no es igualdad |
| `StoreEquipmentLink` | Relación evidenciada y versionada entre Store y equipo | Exacta, temporal, con fuente y estado; nunca por similitud de nombre |
| `CommercialConditionVersion` | Versión inmutable de condiciones comerciales | Vigencia, fuente, moneda/unidad y campos ausentes explícitos |
| `ProtectionAction` | Decisión/acción humana con responsable y compromiso | Idempotente; optimistic concurrency; historial append-only |
| `OutcomeVerification` | Evidencia posterior de transacción, recepción/inventario o fin de penalización | Una señal no sustituye a las demás; cierre exige criterios de la causa |
| `ProtectionMetricSnapshot` | Resultado reproducible de KPI para un corte | Entradas, fórmula, periodo, certeza y estado; no es fuente contable |

Un caso puede referenciar un Store y varias terminales. Un movimiento sin Store
puede originar una alerta de identidad pendiente, pero no se asigna a un comercio.
Una contradicción de serie contra varios Stores bloquea el vínculo y el cálculo
por Store hasta resolución humana evidenciada.

## 3. Contratos de fuente propuestos

Todas las fuentes usan lote inmutable con Organization, hash de bytes, nombre
sanitizado, hoja/fila o coordenada, perfil/version, fecha de recepción, productor,
periodo/corte explícito, moneda/unidad, estado de completitud y procedencia. Un
campo no verificado permanece ausente; no se deriva del nombre del archivo.

| Fuente | Grano y uso | Campos mínimos antes de aceptar | Límites |
| --- | --- | --- | --- |
| Reporte mensual de rentabilidad Netpay | Store-periodo; comisión, beneficio y volumen | Store, periodo, moneda, Volumen, AP, AQ, AR, AS, perfil | AP+AQ+AR; AS separado; v1 no se reinterpreta |
| Liquidación mensual de comisiones y deductivas | Movimiento físico | periodo devengado, entidad, Store opcional, concepto original, importe firmado, moneda, procedencia | Neto reportado no prueba banco; concepto no prueba No Uso |
| Reporte mensual de No Uso | Fila observada por Store/equipo según perfil por verificar | periodo/corte confirmado, identificadores presentes, última actividad si existe, penalización si existe, coordenada | Productor, headers, grano, moneda y campos reales pendientes de Gate A/G |
| Reporte Global de terminales | Observación de equipo | identificadores presentes, estado, corte, procedencia | No se presume Store, MID o serie hasta inspeccionar muestra autorizada |
| Carta/cotización | Documento y versión de condiciones | identidad documental, vigencia, tasa vendida, unidad y moneda; aprobaciones si existen | OCR/extracción no equivale a condición aprobada |
| Cartera/contacto | Master tenant-scoped | Store exacto hacia Branch/Company/Client; presencia de contacto | PII completa sólo en consulta sensible autorizada |
| Seguimiento operativo | Caso y acción append-only | actor, estado anterior/nuevo, responsable, próxima acción, compromiso, nota segura, evidencia | Nota no confirma resultado; PII fuera de eventos/logs |
| Confirmación posterior | Evidencia de transacción, recepción/inventario o no repetición | fuente, fecha/corte, identidad exacta, resultado y procedencia | No inferir depósito, devolución ni fin de penalización de otra señal |

## 4. Identidad y resolución

Estados de vínculo: `unresolved`, `exact_supported`, `ambiguous`,
`contradictory`, `superseded`. La clave de comparación incluye Organization y
la versión de fuente. Store ID exacto puede resolver Store; terminal ID, MID y
serie se resuelven cada uno en su espacio. La evidencia registra lote, fila,
periodo efectivo, actor de confirmación y relación predecesora.

Reglas:

1. no crear ni inferir Store;
2. no usar nombre de comercio como clave;
3. conservar terminales múltiples por Store;
4. no declarar MID canónico sin fuente/autoridad verificadas;
5. detectar una serie simultáneamente asociada a Stores distintos;
6. mostrar sin Store y sin correspondencia en colas separadas;
7. una resolución posterior supersede, no reescribe, la observación anterior.

## 5. Cola operativa

Estados canónicos:

```text
new_alert
identity_pending
contact_pending
ready_to_contact
contact_attempted
reactivation_agreed
return_requested
follow_up
reactivation_verified
equipment_recovered
escalated
closed
not_recoverable
```

Transiciones válidas iniciales:

| Desde | Hacia | Requisito mínimo |
| --- | --- | --- |
| `new_alert` | `identity_pending`, `contact_pending`, `ready_to_contact`, `escalated` | clasificación explícita y versión esperada |
| `identity_pending` | `contact_pending`, `ready_to_contact`, `escalated`, `not_recoverable` | vínculo exacto o razón evidenciada de imposibilidad |
| `contact_pending` | `ready_to_contact`, `escalated`, `not_recoverable` | contacto autorizado disponible o resultado verificable |
| `ready_to_contact` | `contact_attempted`, `escalated` | responsable y próxima acción |
| `contact_attempted` | `reactivation_agreed`, `return_requested`, `follow_up`, `escalated`, `not_recoverable` | resultado de intento sin PII en evento |
| `reactivation_agreed` | `follow_up`, `reactivation_verified`, `escalated` | compromiso y evidencia posterior para verificar |
| `return_requested` | `follow_up`, `equipment_recovered`, `escalated` | recepción/inventario para verificar recuperación |
| `follow_up` | `contact_attempted`, `reactivation_verified`, `equipment_recovered`, `escalated`, `not_recoverable` | siguiente acción vencida/ejecutada explícitamente |
| `reactivation_verified`, `equipment_recovered` | `closed`, `follow_up` | validación financiera posterior o brecha explícita |
| `escalated` | cualquier estado no terminal compatible | decisión humana con razón |
| estados no terminales | `not_recoverable` | razón y evidencia |

`closed` y `not_recoverable` son terminales en el MVP. Reapertura requerirá
comando posterior de supersesión, no edición. Cada mutación exige Organization,
actor, `expected_version`, idempotency key y fingerprint. Replay idéntico retorna
el mismo resultado; clave reutilizada con payload distinto es conflicto. El
historial incluye estado, responsable, próxima acción, fecha compromiso, nota
segura, referencias de evidencia, correlación y causación. Las actualizaciones
concurrentes incompatibles fallan, no last-write-wins.

### Cierre verificable

- Reactivación: transacción posterior vinculada a la terminal/Store y corte
  posterior al acuerdo; si sólo hay Store, la certeza no supera `supported`.
- Recuperación: recepción o inventario con serie/terminal exacta.
- Penalización: al menos un periodo posterior suficiente sin repetición del
  concepto comparable, o evidencia explícita del emisor.
- Cierre financiero: importe observado o cálculo reproducible, periodo y certeza.
- Si falta cualquiera de las evidencias exigidas por la causa, el caso permanece
  en seguimiento o cierra con brecha explícita, nunca como recuperación confirmada.

## 6. Definiciones financieras

| Concepto | Definición | Certeza máxima sin evidencia adicional |
| --- | --- | --- |
| Penalización efectivamente aplicada | Movimiento firmado aceptado y clasificado mediante mapa versionado como penalización, sin doble contabilización | `confirmed` |
| Penalización probable | Cargo o alerta compatible cuyo concepto, periodo o identidad aún no está certificado | `probable` |
| Pérdida calculada por spread | `max(0, tasa_costo_efectiva - tasa_vendida) * base_volumen_compatible` con unidades homogéneas | `supported` |
| Margen dejado de generar | margen de referencia aprobado menos margen observado, aplicado a volumen compatible; null si falta base | `projected` |
| Importe recuperado | mejora financiera observada posterior y atribuible bajo regla aprobada, neta de componentes ya contados | `supported`; `confirmed` sólo con evidencia financiera certificada |
| Penalización evitada | penalización comparable esperada bajo regla aprobada que no aparece después de acción verificada | `projected` salvo confirmación del emisor |
| Rentabilidad protegida | suma disjunta de importe recuperado confirmado/soportado y penalización evitada, menos solapamientos declarados | la menor certeza de sus componentes |

Una cifra participa una sola vez. `rentabilidad protegida` no suma pérdida por
spread, margen dejado de generar e importe recuperado si representan la misma
base. Cada snapshot enumera componentes incluidos y excluidos.

## 7. KPIs del MVP

| KPI | Fórmula propuesta | Fuente primaria | Estado/certidumbre |
| --- | --- | --- | --- |
| Penalizaciones del mes | suma de movimientos comparables clasificados como penalización | liquidación | observado/confirmed; pendientes separados |
| Penalizaciones por No Uso | subconjunto con mapa aprobado a No Uso | liquidación + mapa | observed; null si mapa no aprobado |
| Penalizaciones recurrentes | misma familia comparable y misma identidad en >=2 periodos | liquidaciones | calculated/supported |
| Terminales por reactivar | equipos no terminales con decisión/reactivación pendiente | cola + identidad | calculated |
| Terminales por recuperar | decisiones de devolución sin recepción verificada | cola + inventario | calculated |
| Comercios sin contacto | Stores vinculados sin contacto accesible bajo permiso | Master minimizado | calculated |
| Relaciones Store-serie pendientes | `unresolved + ambiguous + contradictory` | vínculos | observed count |
| Spread esperado | tasa vendida - tasa de costo esperada | condición versionada | calculated |
| Spread efectivo | tasa vendida - tasa de costo efectiva compatible | condición + reporte | calculated |
| Pérdida por spread negativo | `max(0,-spread_efectivo) * volumen_compatible` | condición + rentabilidad | calculated |
| Volumen contra compromiso | volumen observado / volumen comprometido | reporte + condición | no calculable si compromiso <=0/ausente |
| Variación mensual | `(V_t - V_t-1) / V_t-1` | serie Store | no calculable si base cero/ausente |
| Tendencia de tres meses | tres variaciones consecutivas negativas en periodos contiguos | serie Store | calculated; periodos faltantes bloquean |
| Margen dejado de generar | definición de §6 | varias | projected |
| Importe recuperable | suma disjunta de penalización aplicada recuperable y pérdida proyectada accionable | caso + fuentes | projected, nunca caja confirmada |
| Penalización evitada | definición de §6 | periodos posteriores | projected/supported |
| Rentabilidad protegida | definición de §6 | verificaciones | separar observed/calculated/projected |

## 8. Alertas configurables

Los umbrales son configuración versionada con vigencia y Organization; no son
verdades de negocio definitivas:

- volumen cero;
- caída mensual >=30%;
- caída >=80% frente al promedio móvil;
- tres meses consecutivos de reducción;
- volumen <70% del comprometido;
- tasa de costo > tasa vendida;
- spread por debajo del mínimo configurado;
- aumento de costo frente al mes anterior;
- beneficio total combinado negativo;
- misma deductiva comparable durante dos o más periodos.

Cada alerta registra regla/versión, entradas, resultado, periodo, certeza y
explicación. Periodos ausentes no se tratan como cero. Un resultado negativo no
se etiqueta automáticamente como No Uso.

## 9. Seguridad, PII y aislamiento

- `netpay_operations_operator` puede ver PII completa sólo mediante la consulta
  sensible existente y auditada; la cola general muestra presencia/estado.
- Ningún rol o capability se amplía por este documento. Si los contratos de
  mutación no caben en capacidades actuales, Gate A queda BLOCKED y requiere un
  amendment de Governance separado.
- Organization filtra filas, agregados, conteos, eventos, idempotencia y evidencia.
- Recursos ausentes o extranjeros se ocultan según el patrón vigente.
- Nombres, teléfonos y correos reales quedan fuera de logs, eventos y fixtures.
- Exportación y evidencia descargable requieren control de acceso específico;
  no están incluidas en el MVP inicial.

## 10. Contratos candidatos

| ID candidato | Nombre propuesto | Efecto |
| --- | --- | --- |
| `IC-NETPAY-CMD-043` | `AcceptProfitabilityProtectionSource` | aceptar lote/perfil autorizado; no crear Store |
| `IC-NETPAY-CMD-044` | `ResolveStoreEquipmentLink` | confirmar o sustituir mediante supersesión un vínculo exacto o contradicción |
| `IC-NETPAY-CMD-045` | `OpenProfitabilityProtectionCase` | crear alerta/caso idempotente desde evidencia |
| `IC-NETPAY-CMD-046` | `AssignAndPlanProtectionCase` | responsable, próxima acción y compromiso |
| `IC-NETPAY-CMD-047` | `RecordProtectionContactAttempt` | resultado seguro del intento, sin PII en evento |
| `IC-NETPAY-CMD-048` | `DecideEquipmentRecoveryPath` | reactivar, devolver, seguimiento o no recuperable |
| `IC-NETPAY-CMD-049` | `RecordProtectionOutcomeEvidence` | adjuntar referencia y evaluación posterior |
| `IC-NETPAY-CMD-050` | `CloseProfitabilityProtectionCase` | cierre con versión esperada y criterios verificables |
| `IC-NETPAY-QRY-025` | `ListProfitabilityProtectionQueue` | listado minimizado y KPIs filtrados |
| `IC-NETPAY-QRY-026` | `RetrieveProfitabilityProtectionCase` | detalle autorizado e historial |
| `IC-NETPAY-QRY-027` | `RetrieveStoreEquipmentIdentity` | Store-terminal-MID-serie y conflictos |
| `IC-NETPAY-QRY-028` | `RetrieveStoreProfitabilityProtectionMetrics` | serie y snapshots con certeza |
| `IC-NETPAY-QRY-029` | `RetrieveProtectionSourceCoverage` | lotes, perfiles, brechas y pendientes |
| `IC-NETPAY-EVT-031` | `ProfitabilityProtectionSourceAccepted` | lote y perfil aceptados |
| `IC-NETPAY-EVT-032` | `StoreEquipmentIdentityResolved` | vínculo exacto confirmado o supersedido |
| `IC-NETPAY-EVT-033` | `StoreEquipmentIdentityConflictDetected` | ambigüedad o contradicción material |
| `IC-NETPAY-EVT-034` | `ProfitabilityProtectionCaseOpened` | alerta/caso abierto desde evidencia |
| `IC-NETPAY-EVT-035` | `ProfitabilityProtectionActionRecorded` | asignación, plan o intento registrado |
| `IC-NETPAY-EVT-036` | `EquipmentRecoveryPathDecided` | decisión de reactivar, devolver o escalar |
| `IC-NETPAY-EVT-037` | `ProfitabilityProtectionOutcomeVerified` | resultado operativo verificado |
| `IC-NETPAY-EVT-038` | `ProfitabilityProtectionCaseClosed` | cierre y validación financiera declarados |

Gate A debe demostrar consumidor o necesidad de auditoría, esquemas y ausencia
de colisión antes de registrar cada evento.

## 11. Gates A–I

Para cada gate: `PASS` exige ejecución nueva y evidencia; `FAIL` indica criterio
material incumplido; `BLOCKED` indica autoridad, fuente o dependencia ausente.

| Gate | Alcance | PASS | FAIL | BLOCKED |
| --- | --- | --- | --- | --- |
| A — Autoridad, inventario y fuentes | reconciliar autoridad, registro runtime/catálogo, perfiles, campos, head y allowlist | IDs libres, fuente inventariada, autoridad y grafo únicos | colisión, supuesto de campo o alcance no atribuible | fuente/autoridad indispensable inaccesible |
| B — Identidad Store-terminal-serie | modelo y resolución exacta | multi-terminal, sin Store, ambiguos y contradicciones probados | match por nombre, Store creado o contradicción ocultada | ninguna muestra permite validar identificadores |
| C — No Uso y cola | ingestión, penalización, acciones y cierre operativo | estados/transiciones, replay, concurrencia y verificaciones pasan | penalización inferida o cierre sin evidencia | corte/grano de No Uso no confirmado |
| D — Condiciones y spread | versiones, tasas, vigencia y alertas | unidades, vigencia, ausencia y costo>venta probados | fill-zero, mezcla de versiones o doble conteo | documentos/autoridad de condiciones ausentes |
| E — Tendencias | series y reglas configurables | periodos, ceros, faltantes, promedios y tres caídas probados | hueco tratado como cero o umbral fijo sin versión | historia mensual insuficiente |
| F — Seguridad | PII, tenant, capabilities, idempotencia | matriz positiva/negativa, concealment, logs y concurrencia pasan | fuga, escalación o cross-tenant | capability necesaria no autorizada |
| G — Fuentes reales read-only | parser final sobre bytes identificados | hash, estructura, campos, controles y determinismo verificados | pérdida de precisión/procedencia o control material distinto | adjunto/fuente no accesible inequívocamente |
| H — Piloto local/readback | PostgreSQL local aislado, aceptación controlada y UI | un lote, replay/concurrencia, readback y sin efectos externos | duplicación, pérdida o escritura fuera del entorno | infraestructura aislada no demostrable |
| I — UAT | journeys y criterios financieros con usuario | aceptación expresa de flujos, etiquetas y límites | conducta/definición rechazada | datos o actores de UAT no disponibles |

No se puede declarar PASS por tener pruebas escritas, por resultados de IG-015 o
por usar una copia con nombre similar. Gate H no autoriza despliegue ni producción.

## 12. Pruebas mínimas propuestas

- encabezados reordenados/repetidos, ausentes y versiones incompatibles;
- Decimal, signo, moneda, periodo, entidad y procedencia;
- múltiples terminales por Store y una serie contradictoria;
- movimiento/terminal sin Store y Store sin contacto;
- replay idéntico, conflicto de clave y dos comandos concurrentes;
- transición inválida, expected-version conflict e historial append-only;
- cero/ausencia en denominadores, meses faltantes y periodos no contiguos;
- cálculo de spread y prevención de doble contabilización;
- PII minimizada, rol sensible, tenant extranjero y logs/fixtures;
- migración upgrade/downgrade/re-upgrade en PostgreSQL desechable;
- Vitest/Playwright de cola, detalle, permisos y cierre verificable.

## 13. Decisiones pendientes antes de ratificar implementación

1. Campos, grano, productor, corte y moneda reales de No Uso y Global.
2. Fuente autoritativa y temporalidad de terminal, MID y serie.
3. Versiones/unidades de tasas y aprobación de cotizaciones/cartas.
4. Mapa versionado de conceptos de liquidación a penalizaciones de No Uso.
5. Capacidad existente que autorizará `IC-NETPAY-CMD-043..050` o necesidad de gate Governance.
6. Consumidores exactos de `IC-NETPAY-EVT-031..038`.
7. Política de atribución y ventana para importe recuperado/penalización evitada.
8. Periodo del promedio móvil, umbral de casi inactivo y spread mínimo.
9. Evidencia válida de recepción/inventario y confirmación del emisor.

## 14. Allowlist candidata para una primera ratificación

La primera autorización recomendada debe abrir únicamente Gates A y B con
fixtures sintéticos y diseño/persistencia local aislada; no debe aceptar fuentes
reales ni habilitar contacto. La ratificación deberá enumerar archivos después
de inspeccionar el árbol, limitar cualquier migración a PostgreSQL desechable y
mantener cerrados Gates C–I hasta evidencias independientes.
