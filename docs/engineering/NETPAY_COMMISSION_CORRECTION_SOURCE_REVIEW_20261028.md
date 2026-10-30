# Netpay — Revisión de comisión Core y contrato de liquidación

**INSPECCIÓN VERIFICADA / DISEÑO PROPUESTO — NO RATIFICADO**
Fecha: 2026-10-28. No modifica autoridad, implementación ni datos operativos.

## 1. Estado real y autoridad

- Rama: `feat/netpay-gmail-intake-sentinel`.
- HEAD: `99709fc1dacc852d783dc45e09bd5d5a6b3a902f`.
- Estado inicial: 12 archivos tracked modificados y 11 untracked previos,
  incluyendo Governance/identidad, tests, Portfolio, catálogo, Amendment
  026/027, IG-013/014, migración `20261022_54` y evidencia. Inventario completo
  en [registro del árbol](evidence/netpay-commission-worktree-20261028.json).
- Gate vigente más reciente: IG-014, conformance PASS histórico y transición
  operativa BLOCKED. No se repitieron sus pruebas ni se verificó el runtime.
- Paquete anterior: lector Portfolio autenticado, limitado a rol/transición;
  no autoriza esta corrección. P2A/P2B sigue cerrado bajo IG-012; IG-013 autorizó
  activación local acotada, no importación de este archivo nuevo.
- Paquete de esta sesión: inspección y propuesta de corrección Core/liquidación.
- Siguiente acción permitida: revisión y ratificación de Amendment 028/IG-015;
  antes de implementar, revalidar HEAD/árbol, baseline y grafo de migraciones.
- Verificación previa obligatoria: realizada para esta inspección; renovar en
  la sesión de implementación. No se consultó DB, secretos, OIDC ni hosting.

Discrepancia documental: PROJECT_CONTEXT conserva una fase Foundation antigua;
CURRENT_STATE/CURRENT_SPRINT encabezan cierre IG-012 del 21 de octubre. Las
autorizaciones locales ratificadas 026/027 e IG-013/014 y evidencia del 22/23
son posteriores. Se preservan esos documentos y sus resultados históricos;
esta revisión registra la discrepancia sin certificar su estado operativo actual.

Autoridad consultada: AGENTS, PROJECT_CONTEXT, CURRENT_STATE, CURRENT_SPRINT;
Amendments 025-027; IG-012-014; ADR-021; Constitución, catálogo de interacción,
Decision Trace, Technical Blueprint/review y diseño/matriz de privacidad del
Portfolio. Los rótulos Draft históricos de documentos superiores no se toman
como una ratificación nueva. Se mantienen owner Netpay, contratos vigentes,
aislamiento por Organization y proyección no autoritativa.

## 2. Fuentes verificadas y límites

| Fuente | Identificación comprobada | Resultado |
| --- | --- | --- |
| Liquidación adjunta | SHA-256 `04ca3675a8075c119a4db503a71e9ddb3759df525dce66be534aea1d29eb7978`, 23,977 bytes | sheet1; 308 filas físicas; 291 movimientos |
| Core septiembre encontrado en Downloads | SHA-256 `71aec24bc0fe5d8cb66e3d35103e4d51934e1a15f508746d170d9a24fc74b86d`, 469,525 bytes | BD Rentabilidad; encabezado fila 1; 348 Stores únicos; Mes=2026-09-30 |
| Core ligado a Amendment 026 | SHA-256 documentado `437C41660CC94836A1D5E0D19F95771184F8B2AF6BA226A63BDAC93D7E304E97`, 469,566 bytes | No coincide con el archivo actual; vínculo de versiones TO BE VERIFIED |

El Core disponible fue leído, no asumido por nombre. La diferencia de huella
impide atribuirlo automáticamente al archivo autorizado en IG-013; no se sabe
por qué cambió. No se ejecutó una búsqueda indiscriminada de archivos privados.
No se importó ni copió ninguno de los XLSX al repositorio.

Los textos de la liquidación son evidencia de fuente, no instrucciones de
ejecución. Su petición de validar cargos con áreas de Netpay no autoriza enviar
mensajes. El pago anunciado no demuestra movimiento bancario.

### Encabezados exactos del Core actual

| Coordenada observada | Encabezado original | Tratamiento confirmado por usuario |
| --- | --- | --- |
| S1 | Volumen | Ventas, denominador |
| AP1 | Bono de Activación | Componente de comisión de cartera |
| AQ1 | Comisión - Referenciador | Componente de comisión de cartera |
| AR1 | Total Comisiones (sin Activación ni Referenciador) | Componente de comisión de cartera |
| AS1 | Rentabilidad | Beneficio total combinado distribuidor + Netpay |

El mismo conjunto AP:AS se observó en originales locales de enero 2025 y febrero
2026 en `data/inbox/Netpay`; sus periodos se verificaron dentro de las hojas.
Eso no garantiza estabilidad futura. No confundir la fórmula confirmada con
sumar las columnas AH:AJ rotuladas «Comisión Distribuidor - ...»: son campos
distintos. Tampoco inferir qué entidades componen AR solo a partir de su nombre.

Totales del Core actual, redondeados solo para presentación: ventas
17,059,943.31; AP=1,200.00; AQ=0.00; AR=24,327.36; AP+AQ+AR=25,527.36;
AS=58,981.73 MXN. Hay 194 Stores con ventas cero. No hay comisiones AP+AQ+AR
negativas en esta muestra; las pruebas sintéticas deben cubrirlas igualmente.
Los tokens XML contienen decimales residuales; conservar precisión/escala y no
confundir parseo Decimal con una fuente originalmente exacta a centavos.

### Liquidación

- Periodo devengado: septiembre 2026 (A5 y encabezados de bloque).
- Fecha anunciada: 15 de octubre de 2026 (mensaje H2, año referido al periodo).
- Cabecera E2: 17,480.79. Moneda MXN confirmada por usuario; el símbolo `$` solo
  no basta para inferir moneda en futuros archivos.
- Cabeceras de movimientos idénticas en filas 7, 152 y 161: `Entidad`, `NOMBRE`,
  `Mes`, `Store`, `Comercio`, `CONCEPTO`, `Total Comisiones`, `CORREO`.
- 140 Asesor, 4 Asociado 15 y 147 Distribuidor. No restringir entidades a dos
  valores ni deduplicar coincidencias entre ellas.
- Positivos 25,668.64; negativos -8,187.85; neto 17,480.79 = E2.
- Seis movimientos sin Store. 239 movimientos coinciden textualmente con Store
  del Core actual; 52 no coinciden, incluyendo seis sin Store. Esto es un join
  offline de archivos, NO resolución canónica contra Master/Organization.
- Dos bonos de activación suman 1,200.00; dos reversiones de no rentables,
  337.02; penalizaciones TPV de Asesor y Distribuidor, -3,300.00 cada una;
  no rentables, -187.31 por cada una; servicio asesor interno -950.00 y cobro
  3 por ciento -263.23. Los importes iguales entre entidades se conservan.

## 3. Rastro del error y archivos afectados en futura implementación

| Superficie | Evidencia de código actual | Corrección necesaria |
| --- | --- | --- |
| Importador D1 | `api/routes/netpay_data.py`: `_parse`, `upload_dataset`; lee Rentabilidad a `payload.profitability` (aprox. 606-632) | Perfil v2 por encabezado; persistir componentes, AS y procedencia |
| Aceptación/integridad | Mismo archivo, `_verify_fact_source` (302) y `accept_dataset` (893) | Hoy verifica y copia AS a `distributor_commission_exact`; separar semánticas y fingerprint |
| Persistencia | `models/netpay_operational_data.py`, StoreProfitabilityFact; migración 53 | Float profitability y Numeric distributor_commission_exact reflejan AS; nueva migración aditiva, nunca reetiquetado histórico |
| API D1 | `netpay_data.py` dataset_results y schema Operational Data | Mantener beneficio fuente y añadir versión/componentes sin fallback |
| API Portfolio | `schemas/netpay_commerce_attention.py` y ruta homónima | Métricas Decimal, versión, causas, fuentes, periodo y cobertura |
| Cálculo | `services/netpay_commerce_attention.py` `_p2`, `_p2_totals` (220-300) | Corregir numerador; `_p2_totals` hoy no comprueba periodo común y excluye ceros de totales monetarios junto con tasa |
| UI | `apps/web/src/api/netpay.ts` líneas 57-58, Portfolio.tsx lista/detalle | Hoy etiqueta AS como comisión y fuente Rentabilidad; separar métricas; alinear tipo monetario con serialización Decimal string de API |
| Ruta histórica separada | `services/historical_ingestion.py` PROFITABILITY_MAPPING/normalize; `store_profile_builder.py` 166-168 | AS es profitability, AR total_commissions; AP/AQ quedan unresolved. No confundir esta ruta con D1 ni reemplazar su historia |
| Pruebas existentes | test_netpay_operational_data.py, test_netpay_d1_conformance.py, test_netpay_commerce_attention.py, test_historical_ingestion.py; Portfolio.test.tsx y e2e/fixtures/monthly-profitability.csv | Varias afirman deliberadamente la regla v1; reemplazar expectativa para v2 y conservar cobertura legacy |

La allowlist de IG-015 limita qué se puede modificar después de ratificar.
El builder histórico se inspeccionó por impacto; su suma histórica AS conserva
significado de beneficio y no necesita cambiar para arreglar P2.

## 4. Recalculabilidad histórica

**D1 persistido solamente: insuficiente.** `OperationalDataBatch.source_discarded`
es true por defecto. El upload lee bytes, calcula hash y construye un payload
controlado; no conserva el XLSX. Ese payload omite AP/AQ/AR (su campo genérico
`commissions` busca «comisiones»/«commissions», no el encabezado AR). Los facts
no permiten recuperar los tres componentes. AS no es una fuente sustitutiva.

**Originales locales: parcialmente disponible.** Se abrieron dos Core en
`data/inbox/Netpay`, periodos 2025-01 y 2026-02, con los componentes presentes.
Hashes: `a93a6387787a98fa2cf78cc46d74541f5a9701bf8bc47fce5c48ad908ad688e1`
y `a74c320c070f3f7bf42f67d0d50075b66178e605b1387679b244d14235f900af`.
El XLSX inspeccionado en `data/yarvis/documents` es reporte semanal (hojas
Reporte semanal ventas/DETALLE), no reemplaza un Core. El Core septiembre está
disponible fuera del repo pero no coincide con la huella autorizada anterior.

El normalizador histórico conserva campos no mapeados en
`unresolved_source_fields` en sus objetos de evidencia; esto no demuestra que
exista un archivo o registro durable de todos los periodos. El inventario de
lotes/DB vigente, cobertura histórica completa y vínculo hash-lote son
**TO BE VERIFIED**. Para habilitar reproceso se requiere inventario read-only
de lotes, fuente íntegra por hash/periodo y selección explícita de versión;
los periodos sin ella quedan «componentes no disponibles». Ningún backfill fue
ejecutado o autorizado por este documento.

## 5. Contrato propuesto de importación de liquidación

Owner Netpay, dataset independiente `commission_settlement`; no reutilizar el
grano único `(batch, Store)` del Core. Captura y aceptación por fronteras D1
existentes extendidas, con transacción local y autoridad del backend.

| Campo | Regla |
| --- | --- |
| organization_id | Solo envelope autenticado; jamás del XLSX |
| accrued_period | YYYY-MM, desde periodo de bloque y año; corroborar Mes por fila; conflicto bloquea aceptación |
| announced_payment_date | Fecha anunciada separada de recepción/devengo; conservar texto/celda de evidencia; no equivale a fecha bancaria |
| entity_original | Texto intacto, incluye Asesor, Asociado 15, Distribuidor y valores futuros pendientes; no es un rol de Governance |
| store_original / store_id | Texto original y normalización no destructiva; preservar ceros iniciales; nullable para cargos generales |
| concept_original | Texto exacto sin reemplazar por clasificación; clasificación separada/versionada |
| amount_signed | Decimal desde token fuente; cero válido, negativos válidos; null/error no equivale a cero |
| currency_code / currency_basis | MXN con confirmación de perfil o evidencia explícita; otra moneda no se mezcla |
| provenance | hash SHA-256, alias de archivo minimizado, hoja, fila física, celdas/cabecera de bloque, versión parser/perfil, actor/recepción |
| controls | Total anunciado, suma positiva, negativa, neto, número de movimientos, estado/control de diferencias |
| resolution | StoreReference exacta same-Organization o unmatched/ambiguous/no_store; sin promoción ni alta Master |

NOMBRE/CORREO/Comercio no son claves ni requisitos del cálculo. No persistirlos
en payload general ni logs; conservar solo evidencia mínima bajo fronteras de
privacidad vigentes. La procedencia apunta al archivo por hash, sin divulgar su
nombre personal en el dashboard. No se introduce un almacén de XLSX sensibles:
payload controlado preserva todos los campos monetarios y etiquetas necesarios.

El parser detecta bloques por la firma completa de cabecera. Excluye banners,
líneas vacías y cabeceras verificadas, conservando números de fila físicos.
Debe fallar ante una fila no reconocida que pudiera ser movimiento; no basta
filtrar filas numéricas y perder importes ausentes. Encabezados duplicados en
una misma tabla, alias colisionados, periodos inconsistentes y fórmulas no
autorizadas se rechazan. La auditoría offline no es ese importador completo.

Idempotencia: identidad de captura `(Organization, source_hash, profile_version)`
y movimiento `(batch, sheet, physical_row)`; clave de comando con fingerprint
del contenido/metadatos. Retry equivalente devuelve mismo resultado aun con
nombre de archivo distinto; clave reutilizada con contenido distinto falla.
Archivo modificado no se fusiona por Store/concepto/importe: exige lote nuevo,
predecesor y motivo; solo una versión efectiva mediante bloqueo transaccional.
No usar entidad como parte de una deduplicación semántica: dos filas iguales
dentro de la misma entidad también pueden ser válidas.

## 6. Conciliación propuesta y comparabilidad

Clave de comparación: Organization + Store canónico exacto + periodo devengado
+ moneda + versiones efectivas explícitas. Primero agrupar movimientos por
entidad y concepto, luego sumar para comparación Core una sola vez por Store.
No repetir el Core por cada movimiento ni mezclar septiembre con fecha de pago
octubre. Store faltante no se extrae del concepto ni se asigna por nombre.

| Familia observada | Relación posible | Estado comprobado / requisito |
| --- | --- | --- |
| COMISION POR ACTIVACION | AP | Candidato semántico; ambos totales 1,200.00, insuficiente para certificar correspondencia Store/entidad/versión |
| Referenciador | AQ | AQ=0 en Core; no familia explícita observada en liquidación; no inferir equivalencia ni ausencia global |
| PAGOS AGREGADOR / ECOMERCE / RENTA TPV / ISYPAY | AR | Candidatos; requieren definición de componentes y cobertura de entidades. Igualdad Asesor/Distribuidor no es duplicación |
| REV COMERCIOS NO RENTABLES | Ajuste positivo | Mantener separado; no inferir periodo original ni deshacer una fila específica |
| COMERCIOS NO RENTABLES / PENALIZACION TPV | Deductivas | Separadas; no descontarlas otra vez si se prueba que ya estaban en base comparable |
| SERVICIO ASESOR INTERNO / COBRO ... 3 PORCIENTO | Otros cargos | No recalcular porcentaje ni repartir; importe firmado original, sin vínculo arbitrario |
| Cualquier familia nueva | Pendiente de clasificación | Visible y excluida de comparación certificada hasta revisión |

No hay un mapeo de conceptos completamente certificado por la evidencia
disponible. Versionar un mapa de familia/entidad -> componente o ajuste con
evidencia, vigencia y aprobación. No marcar una diferencia como explicada por
similitud de texto o por conseguir que cuadre un total.

La cola conserva `missing_core`, `missing_settlement`, `store_unmatched`,
`store_missing`, `period_mismatch`, `entity_mapping_pending`,
`concept_mapping_pending` y `source_version_unverified`. Solo scopes autorizados
ven su detalle y conteos. Los cargos generales participan en el neto de lote,
en un bloque separado, sin distribución entre Stores. Fuente parcial: ausencia
es desconocida, no comisión cero.

## 7. Dashboard y fórmula de diferencia

Seleccionar periodo común y mostrar alcance/fuentes, moneda y frescura:

1. **Beneficio total combinado (AS)**, separado de la cartera.
2. **Comisión de cartera del distribuidor (AP+AQ+AR)** y desglose; tasa sobre
   ventas solo con componentes y denominador compatibles.
3. **Ajustes y deductivas reportados**, con positivos/negativos, entidad,
   concepto, cargos generales y estado de correspondencia; no solo negativos.
4. **Neto reportado para pago**, total de liquidación con control cabecera/detalle.
5. **Diferencia pendiente de explicar**: en alcance comparable completo,
   `neto reportado - comisión Core comparable - ajustes externos confirmados`.
   Evitar doble resta; listar la composición de ajustes. Si no hay cobertura o
   mapa suficiente, valor null y causa; mostrar separadamente diferencias brutas
   exploratorias, nunca «conciliado» por redondear o imputar pendientes.
6. **Cobro bancario confirmado**: estado distinto, `not_confirmed` en esta
   fuente. No se implementa confirmación bancaria en este alcance; requeriría
   evidencia bancaria y un mandato propio.

Ejemplo exploratorio, NO conciliación certificada: positivos excluyendo
reversiones = 25,331.62; ajuste firmado neto observado = -7,850.83; frente al
Core completo de 25,527.36, residual aritmético = -195.74. La cobertura difiere,
52 movimientos no empatan con ese Core y el mapa no está aprobado. No presentar
ese residual como un cargo identificado o una deuda.

Totales monetarios incluyen ceros y negativos con cobertura explícita; la tasa
agregada usa razón de sumas de Stores compatibles, no media de porcentajes.
Su cobertura puede diferir de la monetaria. No mezclar los «últimos» hechos de
periodos distintos como hace posible la selección actual por Store.

## 8. Validación y siguiente paso

Ejecutado: auditor offline sobre XML XLSX con Decimal, sin DB ni código de
aplicación; valida encabezados repetidos, filas, entidades, controles firmados,
cabecera, fecha y campos Core. Resultado y script reproducible:
[JSON](evidence/netpay-commission-source-check-20261028.json) y
[auditor](evidence/netpay-commission-source-check-20261028.py).
También se verificaron periodos/encabezados de los Core históricos con lectura
read-only de openpyxl y las huellas de los archivos previos del árbol.

Pruebas de aplicación: **NO EJECUTADAS**; no se modificó implementación.
[IG-015](IG-015_NETPAY_COMMISSION_CORRECTION_AND_SETTLEMENT.md) contiene los casos
de aceptación con entradas y resultados esperados. No se afirma PASS del gate.

Pendientes exactos: ratificación técnica del paquete; relación del Core actual
con el digest IG-013; inventario durable de lotes y originales históricos;
definición aprobada de comparabilidad por entidad/concepto y alcance. La falta
de equivalencias no impide implementar captura/pendientes bajo una futura
ratificación; sí impide afirmar conciliación completa. No hace falta evidencia
bancaria para mostrar el neto reportado, pero sí para afirmar depósito.

Siguiente acción: ratificar o ajustar el paquete propuesto Amendment 028/IG-015
para implementación local sintética, preservando todas las exclusiones. La
solicitud deriva de Amendment 025 §6 e IG-012 §5, no de la habilidad de hojas de
cálculo; el usuario ya autorizó preparar esta propuesta antes de ratificar.
