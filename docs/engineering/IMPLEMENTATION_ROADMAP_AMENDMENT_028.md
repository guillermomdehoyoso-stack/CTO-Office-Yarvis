# Amendment 028 — Corrección de comisión Core y liquidación Netpay

**RATIFICADO — IMPLEMENTACIÓN LOCAL Y PRUEBAS SINTÉTICAS SOLAMENTE**
Ratificado por instrucción explícita del usuario el 2026-10-28. La ratificación
abre IG-015 A–E conforme al alcance descrito abajo; mantiene cerradas importación
real, activación, migración productiva, despliegue, commit y push. Los apartados
redactados como propuesta se conservan como alcance ratificado, no como una
ampliación implícita. Ningún PASS técnico se declara por esta ratificación.

Preparado: 2026-10-28. Base inspeccionada: `99709fc1dacc852d783dc45e09bd5d5a6b3a902f`, con trabajo local previo preservado.
Gate propuesto: [IG-015](IG-015_NETPAY_COMMISSION_CORRECTION_AND_SETTLEMENT.md).
Diseño y hallazgos: [revisión de fuentes y contrato](NETPAY_COMMISSION_CORRECTION_SOURCE_REVIEW_20261028.md).

## Decisión solicitada

Ratificar exclusivamente implementación local y conformance sintética de:

1. Perfil Core `netpay_monthly_store_v2`: AS «Rentabilidad» es beneficio total
   combinado del distribuidor y Netpay; comisión de cartera = AP + AQ + AR.
   Nombres verificados: «Bono de Activación», «Comisión - Referenciador» y
   «Total Comisiones (sin Activación ni Referenciador)». Resolver por encabezado
   validado y versión de perfil, nunca por letra de columna.
2. Comisión sobre ventas = suma de esos tres componentes / `Volumen` × 100,
   en la misma Organization, Store, periodo, moneda y versión efectiva.
   Cero de comisión y negativos son valores válidos. Ventas cero, ausencias o
   incompatibilidad producen `No calculable`, valor null y causa explícita.
3. Un perfil separado `netpay_commission_settlement_v1`, un lote de liquidación
   y movimientos inmutables con procedencia. Admitir múltiples movimientos por
   Store, entidad y concepto; no aplicar la unicidad mensual del Core.
4. Conciliación de solo lectura y dashboard con beneficio total, comisión Core,
   ajustes/deductivas, neto reportado, diferencia pendiente y estado bancario
   separado. La comparación entre conceptos requiere un mapeo versionado y
   aprobado; la primera versión puede mostrar correspondencia pendiente.

La corrección de negocio fue confirmada por el usuario el 2026-10-28. Esto no
ratifica por sí mismo esta propuesta técnica. Si se ratifica, sustituye solamente
la semántica `Rentabilidad = comisión` y la exclusión de combinación de campos
de Amendment 025 / IG-012 y su repetición en Amendment 026. Las pruebas y PASS
históricos permanecen como evidencia del comportamiento anterior.

## Gobierno y alcance

Amendment 025 §6 excluye la combinación de comisiones; IG-012 §5 exige una regla
posterior. La nueva fuente y su grano requieren persistencia y controles nuevos.
Por ADR-021 corresponde Amendment + IG (C/D, B para acceso/PII), no una corrección
ligera. Se conserva propietario Netpay, composición read-only del Portfolio y
los patrones transaccionales vigentes; no se propone un ADR ni cambio transversal.

Reutilizar CMD-026..030, QRY-011..013, EVT-015..019 y QRY-023/024 únicamente
extendiendo sus esquemas/perfiles en el propietario existente. No asignar IDs por
tabla. El preflight verificará la correspondencia entre catálogo y registro
runtime: la búsqueda literal de los IDs Netpay ampliados no los encontró en el
catálogo resumido inspeccionado, aunque IG-012 los enumera. No inventar autoridad
ni sobrescribir el cambio local de Governance en ese catálogo.

Permisos actuales conservados: Inbox manage/read para captura y lectura de
lotes; Portfolio read para proyección minimizada; reconciliation.read para
detalle de discrepancias. No añadir roles, grants, OIDC ni reglas de identidad.
No exponer nombre/correo de beneficiario en la proyección general.

## Persistencia propuesta y compatibilidad

- Añadir campos Decimal de los tres componentes, beneficio total AS y versión
  semántica. Conservar tokens/escala originales y procedencia de cada campo.
- El antiguo `distributor_commission_exact` contiene AS. Nunca reinterpretarlo
  ni copiarlo como comisión corregida. V1 conserva su evidencia; en la nueva
  proyección la comisión v1 será null con `commission_components_unavailable`.
  AS puede mostrarse como beneficio total con procedencia v1 explícita.
- Lote de liquidación y movimientos: Organization, archivo hash, hoja/fila,
  periodo, fecha anunciada, entidad original, Store textual opcional, concepto
  original, importe firmado Decimal y moneda. Separar resolución de Store y
  clasificación semántica de la evidencia inmutable.
- Migración aditiva propuesta `20261028_55_netpay_commission_settlement.py`,
  descendiente de `20261022_54` observado localmente. Revalidar unicidad de la
  revisión y grafo antes de crearla; no tocar la migración IG-014 existente.
- Reprocesamiento histórico requiere fuente completa verificable, vínculo al
  lote, predecesor, actor, razón y supersesión explícita. No reconstruir desde
  AS, Float, redondeo visual ni diferencias entre totales. No backfill automático.
- Perfil v2 cambia la semántica del campo público de comisión: respuesta debe
  declarar `metric_definition_version`, componentes y procedencia. Actualizar
  consumidores y pruebas juntos; ningún fallback v1 silencioso.

## Exclusiones y ratificación

Ratificar este paquete no autoriza importar los archivos reales, backfill,
alterar datos operativos, migrar producción, desplegar, commit, push, cobro
bancario, cambios de OIDC/roles/identidad, Gmail, P3-P5, MID, terminales,
comunicaciones ni asignación arbitraria de cargos generales.

Se solicita ratificación conjunta de Amendment 028, IG-015 y el contrato de la
revisión enlazada, limitada a implementación local y pruebas sintéticas. El
hash Core actual difiere del ligado a IG-013; esta propuesta no sustituye la
autorización de aquel archivo ni abre su importación.
