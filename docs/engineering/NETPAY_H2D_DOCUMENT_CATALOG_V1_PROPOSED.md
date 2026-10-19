# Catálogo documental H2-D Netpay — propuesta v1.0.0

Estado del contenido: **APROBADO PARA EL PILOTO — H2-D IMPLEMENTATION IN PROGRESS**
Versión propuesta: `1.0.0`
Fecha efectiva propuesta: `2026-10-14`
Procedencia: `operator_reported`
Propietario aprobado: **Guillermo De Hoyos, responsable operativo de este piloto**

Este artefacto organiza exclusivamente los requisitos aportados por el operador. Guillermo De
Hoyos lo aprobó para este piloto el 2026-10-14 después de verificar el hash canónico; la evidencia
está en `NETPAY_H2D_DOCUMENT_CATALOG_V1_APPROVAL.md`. No representa aprobación corporativa de
Netpay ni permite afirmar que un documento real sea válido, suficiente o vigente.

## Aplicabilidad y alcance

| Clave | Requisito | Alcance propuesto | Persona física | Persona moral | TPV | E-commerce | Antigüedad máxima confirmada |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `applicant_or_representative_government_id` | INE del titular o del representante legal | Titular para persona física; representante legal para persona moral | Sí | Sí | Sí | Sí | No indicada |
| `branch_address_proof` | Comprobante de domicilio del local comercial | Cada local/sucursal; aplicabilidad e-commerce sin local pendiente | Sí | Sí | Sí | Pendiente de confirmar si no hay establecimiento físico | 60 días |
| `receiving_account_bank_statement` | Estado de cuenta bancario | Cliente/cuenta receptora; evidencia compartida entre sucursales que usan la misma cuenta | Sí | Sí | Sí | Sí | 60 días |
| `tax_status_certificate` | Constancia de Situación Fiscal | Cliente/cuenta receptora | Sí | Sí | Sí | Sí | 60 días |
| `branch_premises_photos` | Cuatro fotos por cada sucursal: dos del interior y dos de la fachada | Cada local/sucursal | Sí | Sí | Sí | Pendiente de confirmar si no hay establecimiento físico | No indicada |
| `incorporation_instrument` | Acta constitutiva | Cliente | No | Sí | Sí | Sí | No indicada |
| `legal_representative_authority` | Poder del representante legal | Representante/cliente | No | Sí | Sí | Sí | No indicada |
| `applicant_or_representative_rfc` | RFC del titular o del representante legal | Titular para persona física; representante legal para persona moral | Sí | Sí | Sí | Sí | No indicada |
| `applicant_or_representative_mobile` | Celular del titular o del representante legal | Titular para persona física; representante legal para persona moral | Sí | Sí | Sí | Sí | No indicada |
| `applicant_or_representative_email` | Correo electrónico del titular o del representante legal | Titular para persona física; representante legal para persona moral | Sí | Sí | Sí | Sí | No indicada |
| `branch_manager_contact` | Nombre, teléfono y correo del encargado del comercio | Cada sucursal; una persona puede relacionarse explícitamente con varias | Sí | Sí | Sí | Sí, cuando exista sucursal | No indicada |
| `ecommerce_domain_ownership` | Comprobante de propiedad del dominio | Solicitud e-commerce | No aplica por producto | No aplica por producto | No aplica si sólo TPV | Sí | No indicada |

La estructura propuesta comparte a nivel de cliente y representante el estado de cuenta, la
constancia fiscal, el INE, RFC, datos de contacto, acta constitutiva y poder, según su
aplicabilidad. El comprobante de domicilio, las cuatro fotografías y la relación con un encargado
permanecen como requisitos de cada local/sucursal. Un mismo encargado puede relacionarse con
varias sucursales mediante referencias explícitas a un único juego de datos, sin duplicarlo ni
confundirlo con el titular o representante legal. El comprobante de propiedad del dominio es un
requisito separado que sólo aplica cuando se solicita e-commerce.

Un estado de cuenta se conserva como una sola evidencia compartida cuando varias sucursales usan
la misma cuenta receptora. Cada sucursal debe mantener una referencia explícita a esa evidencia;
no se crean copias del documento.

`No aplica por producto` significa que la regla depende del producto, no del tipo de persona. En
una solicitud mixta TPV/e-commerce el requisito de dominio sí aparece por la parte e-commerce.

## Correspondencia de titulares

La única correspondencia confirmada por la lista aportada es:

- el titular de la Constancia de Situación Fiscal debe corresponder con el titular del estado de
  cuenta bancario.

La revisión debe registrar por separado el titular observado en cada documento y la decisión
humana `coincide`, `no coincide` o `no se pudo determinar`. El catálogo no define coincidencia por
nombre aproximado ni permite inferirla del nombre del archivo. No se exige ninguna otra
correspondencia de titulares en esta propuesta.

## Evaluación de la antigüedad máxima de 60 días

La antigüedad se comprobará **en la fecha de revisión humana del documento**, usando la fecha
registrada por el servidor para esa revisión. Se conservarán:

1. la fecha documental observada;
2. la fecha y zona horaria de revisión;
3. la antigüedad calculada; y
4. la interpretación normativa utilizada.

La antigüedad se calcula en días entre la fecha documental observada y la fecha de revisión humana.
Cumple el criterio temporal cuando el resultado está entre 0 y 60 días, inclusive. Una fecha
documental posterior a la fecha de revisión se registra como observación y no satisface el criterio.
La fecha efectiva propuesta del catálogo no sustituye la fecha de revisión del documento.

Esta regla aplica únicamente a:

- comprobante de domicilio del local comercial;
- estado de cuenta bancario; y
- Constancia de Situación Fiscal.

## Criterios de revisión

Estos criterios describen la revisión humana; no autorizan abrir, descargar, leer u obtener por
OCR el contenido de adjuntos.

| Requisito | Criterios verificables propuestos |
| --- | --- |
| INE | Registrar el titular observado. Para persona física corresponde al titular; para persona moral, al representante legal. |
| Domicilio del local | Registrar la sucursal a la que se atribuye, la dirección observada y su fecha documental; evaluar el límite de 60 días en la fecha de revisión. |
| Estado de cuenta | Registrar titular, cuenta receptora identificable y fecha documental; evaluar el límite de 60 días. Si varias sucursales comparten la cuenta, referenciar una sola evidencia desde cada sucursal. |
| Constancia fiscal | Registrar titular y fecha documental; evaluar antigüedad y comparar explícitamente su titular con el del estado de cuenta. |
| Fotografías | Contabilizar para cada sucursal dos imágenes interiores y dos de fachada. No compartir el cumplimiento entre sucursales. |
| Acta constitutiva | Aplicar sólo a persona moral y registrar revisión humana del requisito. |
| Poder | Aplicar sólo a persona moral y registrar revisión humana del requisito, sin inferir facultades legales no revisadas. |
| RFC | Registrar el RFC observado del titular para persona física o del representante legal para persona moral. |
| Celular y correo | Registrar ambos datos del titular para persona física o del representante legal para persona moral. |
| Encargado del comercio | Registrar nombre, teléfono y correo por cada sucursal. Una persona puede atender varias sucursales mediante relaciones explícitas al mismo contacto; no identificarla automáticamente como titular o representante legal. |
| Propiedad del dominio | Aplicar sólo a e-commerce y registrar el dominio y la evidencia revisada de propiedad; no inferir propiedad por coincidencia del correo o nombre. |

Los nombres de archivo, tipos MIME y metadatos sólo pueden producir `attachment_detected` con una
sugerencia no verificada. `validated` requiere una revisión humana autorizada posterior bajo un
gate que permita el acceso necesario. Los estados documentales conservan el significado fijado
por IG-010: `pending`, `attachment_detected`, `under_review`, `validated`, `observed` y
`not_applicable`.

## Ambigüedad pendiente de aprobación

1. Confirmar la aplicabilidad de comprobante de domicilio, fotografías y datos del encargado para
   e-commerce sin establecimiento físico. Este supuesto queda fuera del alcance inicial propuesto
   y no recibe una regla automática de aplicabilidad.

Esta ambigüedad no agrega excepciones. Los campos afectados deben permanecer pendientes de
decisión y no pueden resolverse automáticamente.

## Cambios incorporados en esta propuesta v1.0.0

- Cuatro fotografías confirmadas para cada sucursal: dos interiores y dos de fachada.
- Vigencia confirmada en 60 días para domicilio, estado de cuenta y constancia fiscal, medida en
  la fecha de revisión humana.
- Estado de cuenta reutilizable como evidencia única cuando varias sucursales comparten la misma
  cuenta receptora, con referencias explícitas desde cada sucursal.
- Para persona física, INE, RFC, celular y correo corresponden al titular; para persona moral se
  conservan como datos del representante legal.
- Nombre, teléfono y correo del encargado se registran por cada sucursal. Una misma persona puede
  atender varias mediante relaciones explícitas sin duplicar sus datos ni confundir sus roles.
- Permanece pendiente únicamente la aplicabilidad para e-commerce sin establecimiento físico.

## Vigencia y reemplazo

La fecha efectiva `2026-10-14` es una propuesta y sólo tendrá efecto si la aprobación explícita la
confirma. La versión aprobada debe ser inmutable. Cualquier cambio de requisito, aplicabilidad,
alcance, antigüedad, correspondencia o criterio de revisión requiere una nueva versión y un nuevo
hash. Una versión posterior no modifica expedientes que ya hayan capturado una instantánea de una
versión anterior.

## Contenido canónico y hash

El contenido canónico es el archivo JSON compañero
`NETPAY_H2D_DOCUMENT_CATALOG_V1_PROPOSED.canonical.json`. El SHA-256 se calcula sobre sus bytes
UTF-8 exactos, con saltos de línea LF y sin BOM. El hash se registra después de generar y verificar
ese archivo.

SHA-256 canónico propuesto:
`4995bf2c1efb96df780249121a68c5d33352eeb5303446638f01a529202c896b`.
