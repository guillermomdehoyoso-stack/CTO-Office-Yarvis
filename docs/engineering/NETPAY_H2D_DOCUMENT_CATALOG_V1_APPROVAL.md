# Aprobación operativa del catálogo documental H2-D Netpay v1.0.0

Estado: **APROBADO PARA EL PILOTO — AUTORIDAD OPERATIVA, NO APROBACIÓN CORPORATIVA NETPAY**
Fecha de registro: `2026-10-14`
Fecha efectiva: `2026-10-14`
Versión: `1.0.0`
Propietario y aprobador nominal: **Guillermo De Hoyos, responsable operativo de este piloto**
Procedencia del contenido: `operator_reported`
## Artefacto aprobado

- Archivo canónico: `NETPAY_H2D_DOCUMENT_CATALOG_V1_PROPOSED.canonical.json`
- SHA-256 aprobado: `4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b`
- SHA-256 verificado antes de registrar esta aprobación:
  `4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b`
- Resultado: **coincidencia exacta**.
- Canonicalización: bytes exactos UTF-8, saltos LF, sin BOM.

El nombre histórico del archivo conserva `PROPOSED` porque esos son los bytes sometidos y
aprobados. Esta evidencia registra su transición de gobierno sin alterar la instantánea ni su
hash.

## Alcance aprobado

- persona física y persona moral;
- TPV, e-commerce y mixto cuando existen locales físicos;
- requisitos de cliente/cuenta receptora, titular o representante legal y cada sucursal;
- contactos de encargado relacionados explícitamente por sucursal;
- evidencia bancaria compartida mediante referencias, sin duplicar el documento;
- antigüedad máxima de 60 días evaluada en la fecha de revisión humana; y
- correspondencia humana entre el titular de la Constancia de Situación Fiscal y el titular del
  estado de cuenta.

E-commerce sin establecimiento físico permanece excluido. Adjuntos/OCR, Drive y P2 permanecen
cerrados. Esta aprobación no permite inferir validez por nombre o MIME, descargar o leer adjuntos,
ni atribuir aprobación corporativa de Netpay.

## Efecto de gate

Con H2-I PASS ya registrado y este catálogo aprobado por un responsable nominal, se satisfacen las
condiciones documentales de entrada de IG-010 para abrir **H2-D IMPLEMENTATION IN PROGRESS**.
H2-D todavía no es PASS. El cierre exige la instantánea versionada e inmutable, los seis estados,
historial append-only, aislamiento, idempotencia, readback/reload, completitud y bloqueadores,
incluida una prueba mixta con cinco sucursales sin mutaciones Master ni acceso a adjuntos.
