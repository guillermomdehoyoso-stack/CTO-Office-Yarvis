# Yarvis Domain Model

## 1. Propósito
Definir el modelo conceptual mínimo del dominio operativo de Yarvis para el Foundation Sprint.

---

## 2. Núcleo del dominio

### Organization
Representa una empresa, negocio o unidad de negocio.

- identidad: id, nombre, tipo, estado;
- responsabilidad: agrupar personas, Casos y documentos;
- invariantes: debe tener un nombre único.

### Person
Representa a una persona física.

- identidad: id, nombre completo, correos, teléfonos;
- responsabilidad: participar en relaciones y estar asociada a Casos;
- invariantes: debe existir un identificador único.

### ContactPoint
Representa un medio de contacto de una persona u organización.

- identidad: id, tipo, valor, preferido;
- responsabilidad: normalizar canales de comunicación;
- invariantes: un contacto debe tener un tipo y valor.

### Relationship
Representa la relación entre actores y organizaciones.

- identidad: id, tipo, origen, destino;
- responsabilidad: describir rol y vínculo operativo;
- invariantes: debe referenciar entidades válidas.

### BusinessUnit
Representa una línea de negocio o unidad operativa.

- identidad: id, nombre, organización;
- responsabilidad: agrupar procesos y Casos;
- invariantes: debe pertenecer a una organización.

### Product
Representa un producto o servicio ofrecido.

- identidad: id, nombre, tipo, unidad de negocio;
- responsabilidad: contextualizar Casos y oportunidades;
- invariantes: debe tener un nombre y un tipo.

### Case
Representa una necesidad, solicitud, oportunidad, incidencia, trámite o resultado esperado.

- identidad: id, readable_id, título, descripción;
- responsabilidad: centralizar seguimiento operativo;
- invariantes: debe pertenecer a una organización y tipo de Caso.

### CaseType
Define la plantilla operativa de un Caso.

- identidad: id, nombre, código;
- responsabilidad: fijar checklist, etapas y reglas;
- invariantes: debe existir un workflow asociado.

### CaseStage
Representa una etapa del ciclo de vida de un Caso.

- identidad: id, clave, nombre, orden;
- responsabilidad: ordenar transiciones;
- invariantes: debe existir dentro de un tipo de Caso.

### CaseStatus
Representa un estado ejecutivo del Caso.

- identidad: id, clave, nombre;
- responsabilidad: indicar situación operativa;
- invariantes: debe ser consistente con la etapa.

### Project
Agrupa varios Casos cuando se requiere coordinación superior.

- identidad: id, título, organización;
- responsabilidad: agrupar ejecución y seguimiento;
- invariantes: puede existir sin Casos asociados.

### Dossier
Agrupa documentos y evidencias dentro de un Caso.

- identidad: id, título, caso;
- responsabilidad: construir expediente documental;
- invariantes: debe pertenecer a un Caso.

### Document
Representa un documento o evidencia asociada a un Caso.

- identidad: id, nombre original, nombre normalizado, tipo, almacenamiento;
- responsabilidad: conservar evidencia y metadatos;
- invariantes: debe estar asociado a un Caso y a un expediente.

### DocumentType
Clasifica documentos por finalidad o naturaleza.

- identidad: id, nombre, código;
- responsabilidad: normalizar tipos documentales.

### Evidence
Representa una pieza de información con valor operativo, pudiendo ser un documento, imagen o registro.

- identidad: id, tipo, fuente, hash;
- responsabilidad: conservar evidencia verificable;
- invariantes: debe tener un origen y un estado de validación.

### ChecklistTemplate
Define la estructura de requisitos para un tipo de Caso.

- identidad: id, nombre, tipo de Caso;
- responsabilidad: configurar requisitos reutilizables;
- invariantes: debe poder extenderse por tipo.

### ChecklistRequirement
Representa un requisito concreto del checklist.

- identidad: id, código, etiqueta, obligatorio;
- responsabilidad: expresar lo que debe completarse;
- invariantes: debe pertenecer a un checklist.

### RequirementFulfillment
Registra el cumplimiento real de un requisito.

- identidad: id, requisito, caso, documento, estado;
- responsabilidad: mostrar avance y bloqueos;
- invariantes: debe tener un estado válido.

### Action
Representa una tarea o acción pendiente.

- identidad: id, título, responsable, estado, fecha esperada;
- responsabilidad: mover la ejecución del negocio;
- invariantes: debe tener una intención operativa clara.

### Commitment
Representa un compromiso de una persona u organización respecto a un Caso.

- identidad: id, actor, descripción, fecha esperada, estado;
- responsabilidad: explicitar obligaciones.

### Dependency
Representa una dependencia entre Casos, acciones o partes interesadas.

- identidad: id, origen, destino, tipo;
- responsabilidad: identificar bloqueos y coordinación;
- invariantes: debe describir una relación real.

### Event
Representa un cambio relevante a registrar.

- identidad: id, tipo, payload, correlación;
- responsabilidad: auditar y reconstruir historia;
- invariantes: debe ser inmutable.

### Decision
Registra una decisión relevante del negocio.

- identidad: id, asunto, resumen, aprobador;
- responsabilidad: preservar criterio y contexto;
- invariantes: debe estar ligada a un Caso o proyecto.

### Opportunity
Representa una oportunidad comercial o de crecimiento.

- identidad: id, tipo, estado, valor estimado;
- responsabilidad: conectar operaciones con negocio;
- invariantes: debe derivarse de contexto operable.

### Interaction
Representa una interacción con un actor, canal o sistema.

- identidad: id, tipo, fuente, fecha;
- responsabilidad: capturar entrada del flujo natural de trabajo;
- invariantes: debe tener un origen.

### Conversation
Representa un hilo de conversación o intercambio asociado a un Caso.

- identidad: id, caso, origen;
- responsabilidad: conservar contexto conversacional.

### CostCenter
Agrupa costos para contabilidad o análisis.

- identidad: id, nombre, tipo;
- responsabilidad: asignar gastos.

### ValueCenter
Agrupa valor o rentabilidad por unidad de negocio o proyecto.

- identidad: id, nombre, tipo;
- responsabilidad: medir impacto de valor.

### FinancialMovement
Registra un movimiento financiero relevante.

- identidad: id, tipo, monto, fecha, caso;
- responsabilidad: rastrear flujo y rentabilidad;
- invariantes: debe estar asociado a un Caso o centro de costo.

### CostItem
Representa un costo real o estimado.

- identidad: id, categoría, monto, evidencia;
- responsabilidad: alimentar control financiero.

### RevenueItem
Representa un ingreso o comisión esperada o real.

- identidad: id, categoría, monto, caso;
- responsabilidad: alimentar rentabilidad y tesorería.

### PaymentMilestone
Representa un hito de cobro o pago.

- identidad: id, caso, fecha esperada, monto;
- responsabilidad: modelar flujo de caja;

### ProviderQuote
Representa una cotización de proveedor.

- identidad: id, proveedor, monto, caso;
- responsabilidad: comparar costos reales y estimados.

### BillOfMaterials
Representa una lista de materiales para un proyecto.

- identidad: id, caso, versión;
- responsabilidad: comparar estimación, cotización y ejecución.

### BillOfMaterialsItem
Representa un elemento concreto del BOM.

- identidad: id, producto, cantidad, costo;
- responsabilidad: analizar variaciones.

### TechnicalAssessment
Representa la evaluación técnica de una instalación o propuesta.

- identidad: id, caso, resumen, fecha;
- responsabilidad: captar variables técnicas del negocio.

### Site
Representa un lugar físico de instalación o visita.

- identidad: id, nombre, dirección, caso;
- responsabilidad: contextualizar levantamientos y visitas.

### Measurement
Representa una medición o variable técnica.

- identidad: id, tipo, valor, unidad, sitio;
- responsabilidad: alimentar evaluación y diseño.

### Integration
Representa una integración externa o futuro conector.

- identidad: id, nombre, tipo, estado;
- responsabilidad: desacoplar proveedores externos.

### AuditEntry
Registro inmutable de cambios relevantes.

- identidad: id, entidad, acción, usuario, correlación;
- responsabilidad: auditar operaciones y decisiones.

### User
Representa el usuario del sistema.

- identidad: id, nombre, correo, rol;
- responsabilidad: identificar quién realiza acciones.

### Role
Representa un rol del sistema.

- identidad: id, nombre;
- responsabilidad: agrupar permisos.

### Permission
Representa un permiso del sistema.

- identidad: id, nombre, módulo;
- responsabilidad: controlar acceso a capacidades.

---

## 3. Relaciones clave
- Organization tiene muchas Person y many Case.
- Case pertenece a uno o varios BusinessUnit y a un CaseType.
- Case tiene muchos Document, Action, Dependency, Event y RequirementFulfillment.
- Dossier agrupa Document.
- Project agrupa Case.
- FinancialMovement y CostItem alimentan análisis de rentabilidad y tesorería.

---

## 4. Invariantes iniciales
- Todo Caso debe pertenecer a una organización y a un tipo de Caso.
- Todo documento debe asociarse a un Caso y a un expediente.
- Toda acción debe tener un responsable o un responsable delegado.
- Toda transición de etapa debe generar un evento y una entrada de auditoría.
- Toda acción sensible requiere confirmación humana o política explícita.

---

## 5. Eventos principales
- case.created
- case.stage.changed
- document.received
- checklist.requirement.completed
- next.action.created
- dependency.blocked
- decision.recorded

---

## 6. Ciclo de vida inicial
1. Ingreso de documento o mensaje.
2. Clasificación y asociación.
3. Actualización de checklist.
4. Evaluación de etapa.
5. Creación de acción siguiente.
6. Auditoría y confirmación.

---

## 7. Dudas abiertas
- Si el modelo de negocio requiere separar Person y Actor como conceptos distintos o si pueden unificarse en la primera iteración.
- Si los Casos se modelan como agregados raíz o si la separación entre Case y Project debe ser más estricta.
- Si se necesita un modelo financiero completo desde el inicio o solo un subconjunto mínimo para el Foundation Sprint.
