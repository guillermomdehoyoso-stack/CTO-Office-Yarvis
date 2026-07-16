# Yarvis Operational Identity Resolution v1.0

## 1. Purpose

Yarvis must identify persons, companies, merchants, branches, stores and assets correctly from fragmented operational information.

Identity resolution is distinct from:

- extraction;
- classification;
- parsing;
- OCR;
- search;
- entity creation.

## 2. Core Principle

Observations are evidence, not identity.

An observation does not automatically become a confirmed identity.

Approved commercial hierarchy reference:

ClientAccount
-> Company
-> Branch
-> Store
-> Asset

## 3. Identity Layers

### Organization

Entidad legal o comercial principal.

Ejemplos:

- cliente;
- proveedor;
- socio;
- razón social.

Identificadores posibles:

- UUID interno;
- RFC;
- razón social;
- nombre comercial;
- dominio;
- cuenta bancaria;
- correo corporativo.

### Person

Contacto humano.

Identificadores:

- UUID interno;
- nombre;
- correo;
- teléfono;
- rol;
- organización.

### Client

Relación comercial de medios de pago.

Puede pertenecer a una Organization.

Identificadores:

- Client ID;
- número de comercio;
- razón social;
- nombre comercial.

No asumir que Client y Organization son siempre equivalentes.
One Client ID may map to multiple Companies, and one Company may map to multiple Stores through different Branches.

### Branch

Ubicación física o unidad operativa.

Identificadores:

- domicilio;
- sucursal;
- ciudad;
- teléfono;
- referencias;
- nombre interno.

### Store

Registro operativo de NetPay.

Identificadores:

- Store ID;
- producto;
- estatus;
- Client;
- Branch;
- Organization.

Un Store puede ser:

- TPV;
- eCommerce;
- link;
- otro producto.

Un Store no debe confundirse con una sucursal física.

### Asset

Recurso físico o técnico administrado.

Ejemplos:

- TPV;
- inversor;
- cargador;
- medidor;
- DTU;
- módem.

Identificadores:

- serie;
- modelo;
- fabricante;
- QR;
- identificador de plataforma.

### Shipment

Movimiento logístico.

Identificadores:

- número de guía;
- transportista;
- destinatario;
- domicilio;
- fechas.

### Service Case

Caso externo u operativo.

Identificadores:

- folio;
- sistema origen;
- tipo;
- fecha;
- estado.

## 4. Recipient Separation

### Email Recipient

Buzón o persona que recibió el correo.

### Operational Recipient

Área o responsable que debe procesar el caso.

### Logistics Recipient

Persona o empresa que recibe o entrega físicamente el activo.

### Physical Destination

Sucursal o domicilio donde termina el activo.

Nunca asumir que son equivalentes.

## 5. Identifier Strength

### Strong identifiers

- UUID interno
- Store ID
- Client ID
- serial
- RFC confirmado
- folio oficial
- tracking number cuando es único en el carrier

### Medium identifiers

- correo
- teléfono
- dominio
- domicilio estructurado
- combinación nombre + sucursal

### Weak identifiers

- nombre aislado
- razón social aproximada
- texto OCR
- asunto del correo
- referencias informales
- alias no confirmados

La fortaleza depende del contexto y no debe ser una constante universal.

## 6. Observation Model

Cada observación debe contener conceptualmente:

- observed_value
- normalized_value
- identifier_type
- source_type
- source_reference
- extraction_method
- confidence
- observed_at
- candidate_entity_type
- candidate_entity_id
- confirmation_status
- confirmed_by
- confirmed_at
- rejection_reason
- supersedes_observation_id

No implementar aún una tabla genérica si no es necesaria.

## 7. Resolution Process

Flujo:

1. Capture
2. Normalize
3. Extract
4. Generate candidates
5. Score candidates
6. Detect conflicts
7. Present suggestion
8. Human confirmation
9. Persist relationship
10. Emit Domain Event

## 8. Candidate Scoring

Factores:

- coincidencia de identificador fuerte;
- coincidencia de Store ID;
- serie;
- RFC;
- folio;
- destinatario;
- dirección;
- teléfono;
- correo;
- historial;
- fuente;
- fecha;
- consistencia con casos previos.

No definir todavía un algoritmo de machine learning.

Usar reglas deterministas y explicables primero.

## 9. Conflict Handling

Ejemplos:

- misma serie asociada a dos Stores activos;
- mismo Store ID con dos clientes;
- mismo domicilio con varias sucursales;
- guía con destinatario distinto al cliente;
- correo reenviado;
- RFC distinto entre documentos;
- activo enviado pero no confirmado como entregado.

Estados:

- unresolved
- needs_review
- accepted_exception
- corrected
- historical

Nunca borrar silenciosamente el conflicto.

## 10. Provenance

Toda identidad resuelta debe poder responder:

- qué fuente lo indicó;
- cuándo;
- con qué confianza;
- qué parser o proveedor lo produjo;
- quién confirmó;
- qué observaciones fueron rechazadas.

## 11. Domain Ownership

### Parser

Extrae valores.

No resuelve identidades definitivas.

### Document Intelligence

Extrae texto y candidatos.

No crea entidades finales.

### Identity Resolver

Propone coincidencias y detecta conflictos.

### Domain Engine

Autoriza cambios de relación.

### Human Reviewer

Confirma o rechaza cuando corresponde.

### Persistence

Conserva hechos, observaciones, decisiones y eventos.

## 12. NetPay Example

Correo NetPay:

- folio CAS-12345;
- guía 784563221;
- destinatario logístico Juan Pérez;
- empresa Gasolineras del Valle;
- sucursal Metepec;
- Store ID 503218;
- serie A920-XYZ123.

Yarvis debe:

1. crear o localizar Service Case;
2. localizar Shipment;
3. buscar Organization candidata;
4. buscar Client candidato;
5. buscar Branch canidata;
6. buscar Store candidato;
7. buscar Asset candidato;
8. proponer relaciones;
9. marcar conflictos;
10. esperar confirmación;
11. emitir eventos;
12. mantener provenance.

## 13. Sprint 7.2 Implementation Note

Observation and resolution records are persisted explicitly and keep provenance, confidence, confirmation status, and auditable confirmation metadata.

Automatic parser output remains candidate until explicit confirmation when identity or ownership is affected.

## 13. Asset Strategy

Establecer:

- Asset es el término arquitectónico general.
- Device puede permanecer como nombre específico dentro de NetPay.
- No realizar migración prematura.
- Evaluar entidad Asset general cuando exista un segundo dominio real que la necesite.
- La futura entidad Asset no debe depender de NetPay.

## 14. API Guidance

Evitar que cada fuente cree su propio conjunto independiente de endpoints.

Preferir:

- Intake;
- Cases;
- Identity Suggestions;
- Confirmations;
- Timeline;
- Evidence.

Los endpoints específicos NetPay actuales pueden conservarse durante el MVP.

Documentar como deuda:

- consolidar convenciones;
- evitar proliferación CRUD;
- separar comandos de consultas;
- mantener eventos como trazabilidad.

## 15. Privacy and Security

- datos de identidad se clasifican según AI_DATA_HANDLING_POLICY;
- no enviar datos Confidential o Restricted a servicios externos sin autorización;
- redactar logs;
- no guardar bodies completos en eventos;
- conservar acceso mínimo;
- confirmación humana para uniones sensibles;
- no exponer domicilios o teléfonos públicamente.

## 16. Future Evolution

Registrar sin implementar:

- IdentityObservation persistente;
- IdentityCandidate;
- Identifier;
- Alias;
- Merge Proposal;
- Split Proposal;
- Conflict;
- Asset general;
- Organization/Branch/Store graph;
- deterministic resolver;
- probabilistic resolver;
- semantic matching;
- human review queue.

## 17. Non-goals

No implementar ahora:

- graph database;
- entity resolution con IA externa;
- machine learning;
- auto-merge irreversible;
- Asset general;
- migraciones nuevas;
- renombrado masivo;
- Portal NetPay;
- Gmail;
- browser automation.

## 18. Acceptance Rules

El documento debe dejar claro:

- extraction ≠ identity;
- email recipient ≠ operational recipient;
- logistics recipient ≠ physical destination;
- Store ≠ Branch;
- Clientt ≠ Organization;
- Device específico NetPay ⊂ Asset general;
- confirmed human data wins;
- conflicts are retained;
- provenance is mandatory.