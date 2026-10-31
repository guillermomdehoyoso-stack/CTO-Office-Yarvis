# Amendment 029 — Protección y recuperación de rentabilidad Netpay

**RATIFIED — IMPLEMENTATION AUTHORITY FOR GATES A AND B ONLY**

Ratificado por instrucción explícita del usuario el 2026-10-30. Gates C–I,
fuentes reales, importación, despliegue y activación permanecen cerrados. El
cierre técnico, commit y push de Gates A/B fueron autorizados separadamente el
2026-10-31 sin ampliar el alcance funcional.

Fecha de propuesta: 2026-10-30

Base documental inspeccionada: `5c5cb8c4a93a96754b2e8c273b315e2da68fc68a`

Gate propuesto: [IG-016](IG-016_NETPAY_PROFITABILITY_PROTECTION_AND_RECOVERY_MVP.md)

Revisión de fuentes: [fuentes y brechas](NETPAY_PROFITABILITY_PROTECTION_SOURCE_GAP_REVIEW_20261030.md)

## 1. Decisión solicitada

La decisión ratificada autoriza exclusivamente la base local y sintética de
Gates A/B para un futuro MVP que convierta deterioros de rentabilidad observados
en trabajo operativo trazable y en resultados financieros verificables:

```text
penalización o deterioro
  -> Store
  -> terminal / MID / número de serie
  -> comercio y contacto
  -> acción responsable
  -> resultado operativo
  -> validación financiera posterior
```

La propuesta no transfiere propiedad entre contextos. Netpay Merchant Operations
conserva el Store, las fuentes Netpay y la cola especializada. Master conserva
comercio y contacto. Operational Data conserva lotes y hechos observados.
Operational Economics sigue siendo el único propietario de hechos económicos
genéricos; este MVP calcula proyecciones Netpay con procedencia y no crea un
ledger, depósito bancario ni roll-up económico implícito.

## 2. Alcance propuesto

### IG-016A — No Uso y recuperación

- ingestión controlada del Reporte mensual de No Uso;
- identidad exacta Store-terminal-MID-serie, con ambigüedad visible;
- penalización aplicada o probable y última actividad disponible;
- decisión humana de reactivar o recuperar equipo;
- responsable, siguiente acción, compromiso e historial append-only;
- verificación posterior por transacciones, recepción/inventario y no repetición
  de la penalización.

### IG-016B — Condiciones comerciales y spread

- versión de carta o cotización, vigencia y procedencia;
- tasa vendida, costo esperado, costo efectivo, volumen comprometido, giro e
  incentivo solicitado/autorizado;
- spread esperado y efectivo sin completar datos ausentes con cero;
- alerta cuando costo supera venta y causa inicial `pending_validation`;
- revisión humana de giro, incentivo, tasa o condiciones.

### IG-016C — Tendencias de volumen

- serie mensual por Store desde el Reporte mensual de rentabilidad Netpay;
- variación mensual, promedio móvil, comparación con compromiso, tres caídas
  consecutivas y actividad cero o casi inactiva;
- impacto monetario estimado, contacto y plan de recuperación.

## 3. Autoridad, contratos e identificadores

La inspección del repositorio encontró libres Amendment 029 e IG-016. El registro
runtime Netpay vigente llega a `IC-NETPAY-CMD-042`, `IC-NETPAY-QRY-024` e
`IC-NETPAY-EVT-030`. El catálogo arquitectónico resumido no refleja todavía todo
ese registro; Gate A debe reconciliar ambos antes de exponer un contrato nuevo.

Rangos candidatos, no registrados ni autorizados por esta propuesta:

| Rango | Uso propuesto |
| --- | --- |
| `IC-NETPAY-CMD-043..050` | aceptar fuente versionada; resolver vínculo de terminal; abrir alerta; asignar/planear; registrar intento; decidir reactivación/devolución; registrar evidencia; cerrar con verificación |
| `IC-NETPAY-QRY-025..029` | cola; detalle; identidad Store-terminal; serie financiera/KPIs; fuentes y brechas |
| `IC-NETPAY-EVT-031..038` | fuente aceptada; identidad resuelta/contradictoria; alerta creada; acción registrada; decisión registrada; reactivación/equipo verificado; cierre financiero validado |

No se crea contrato para filtros, columnas, orden, navegación o visualizaciones.
Cada evento requiere consumidor o necesidad de auditoría. Los nombres, esquemas,
capacidades y asignación individual de estos IDs quedan sujetos a ratificación.

El grafo observado tiene un solo head, `20261028_55`. Una futura migración sería
candidata a `20261030_56_netpay_profitability_protection.py`, descendiente directa
de 55. El identificador no queda reservado; debe revalidarse al abrir Gate A.

## 4. Reglas financieras que no pueden cambiar

- Comisión del distribuidor = AP + AQ + AR.
- AS es beneficio total combinado del distribuidor y Netpay.
- Ventas cero producen porcentaje no calculable.
- Históricos v1 permanecen pendientes de reprocesamiento cuando falten originales.
- Neto reportado para pago no equivale a depósito bancario confirmado.
- Un importe negativo no demuestra por sí solo una terminal sin uso.
- Concepto, signo, periodo, entidad, moneda y procedencia se conservan.
- No se suman componentes superpuestos ni se fuerza una conciliación para cuadrar.

Las cifras se separan en `observed`, `calculated` y `projected`, y cada resultado
declara certeza (`confirmed`, `supported`, `probable`, `unknown`) y entradas.

## 5. Identidad, seguridad y privacidad

Store ID es la identidad comercial primaria cuando existe. Terminal, MID y serie
son identidades separadas; un Store puede tener varias terminales. Sólo se crea
un vínculo con evidencia exacta y versionada. Nombre, teléfono, dirección o
similitud no son claves. Una serie ligada a varios Stores queda contradictoria y
bloqueada. Registros sin Store permanecen visibles; este paquete no crea Stores.

La PII completa se limita al rol existente `netpay_operations_operator` mediante
las capacidades sensibles vigentes. El listado general permanece minimizado.
No se amplían roles, OIDC, grants ni capacidades sin un gate específico. Logs,
eventos, métricas y fixtures no incluyen nombres, correos o teléfonos reales.
Toda lectura y mutación se aísla por Organization y deniega por defecto.

## 6. Gates propuestos

IG-016 define Gates A–I independientes. La ratificación deberá indicar cuáles
abre y con qué allowlist. Ningún PASS puede provenir de pruebas preparadas,
resultados históricos o una fuente parecida. Gate G es lectura real; Gate H es
piloto local controlado; Gate I es UAT. Ninguno implica producción.

## 7. Fuera de alcance

Reprocesamiento histórico masivo; inferencia automática de Store; MID canónico
sin evidencia; mensajería automática; confirmación bancaria automática;
despliegue productivo; activación multiusuario; P3–P5; D2-Lite; modelos
predictivos; cambio automático de tasas/condiciones; creación de Store; edición
de datos fuente; importación real por esta propuesta; y cualquier cambio de
OIDC, roles o identidad.

## 8. Efecto de ratificación

Esta ratificación autoriza únicamente la implementación local, migración
`20261030_56` y pruebas sintéticas de Gates A/B descritas por IG-016. No autoriza
fuentes reales, importación, operación ni Gates C–I. El cierre y publicación en
el repositorio no equivalen a despliegue o activación. IG-014 e IG-015 permanecen
cerrados e intactos; Amendment 028 e IG-015 prevalecen sobre la antigua
interpretación de AS.
