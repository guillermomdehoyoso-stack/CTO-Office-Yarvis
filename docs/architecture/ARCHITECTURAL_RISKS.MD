# Architectural Risk Register

## R001 — Dependencia del Connector para contexto de negocio

**Estado**
Open

**Probabilidad**
Alta

**Impacto**
Alto

**Descripción**

Los conectores (Huawei, Solis, etc.) pueden no proporcionar toda la información necesaria para modelar correctamente el dominio de negocio (Owner, Project, Site, Asset ownership, MRV boundaries, etc.).

**Consecuencia**

Energy Tracer quedaría acoplado a la ontología del fabricante, dificultando:

- Multi-cliente
- Multi-fabricante
- Cambios de propietario
- Fusiones de plantas
- Auditoría
- Digital Evidence

**Mitigación propuesta**

Crear un Context Registry interno compuesto por:

- Organization
- Project
- Site
- Asset
- Asset Identifier
- Connector
- Data Stream

Los connectors únicamente aportan datos técnicos e identificadores externos.

**Owner**

CTO

**Sprint objetivo**

Sprint 06D

**Estado**

Open

---

## R002 — Security, Privacy and Trust

**Estado**

Open

**Probabilidad**

Alta

**Impacto**

Muy alto

**Descripción**

Riesgo estratégico de primer nivel que agrupa amenazas sobre credenciales, secretos, documentos, acceso, continuidad operativa y confianza institucional.

### R002.1 — Fuga de credenciales

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: variables de entorno, revisión manual, separación de servicios locales.
- Mitigación futura: secret manager formal, rotación de credenciales y detección de exposición.
- Señal de activación: credenciales visibles en repositorio, logs o artefactos compartidos.

### R002.2 — Secretos en Git

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: `.gitignore`, revisión manual y disciplina operativa.
- Mitigación futura: escaneo automático de secretos y políticas de pre-commit.
- Señal de activación: aparición de claves, tokens o passwords en diffs o historial.

### R002.3 — Acceso indebido a datos

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: entorno local no expuesto públicamente, validación de referencias y acceso físico controlado al equipo.
- Mitigación futura: autorización granular, RBAC y policy checks por entidad.
- Señal de activación: usuarios pueden leer o modificar datos fuera de su alcance autorizado.

### R002.4 — Pérdida o robo del equipo

- Probabilidad: Media.
- Impacto: Alto.
- Mitigación actual: servicios contenidos localmente y superficie externa reducida; no existe aún una mitigación suficiente ante robo del equipo.
- Mitigación futura: cifrado de disco, autenticación fuerte y gestión remota de acceso.
- Señal de activación: equipo perdido, robado o comprometido sin revocación inmediata.

### R002.5 — Pérdida o corrupción de la base de datos

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: PostgreSQL con volumen persistente y migraciones controladas.
- Mitigación futura: backups automatizados, restauración ensayada y verificación periódica.
- Señal de activación: errores de integridad, pérdida de datos o imposibilidad de restaurar.

### R002.6 — Backups no cifrados

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: backups limitados al entorno local y control manual.
- Mitigación futura: cifrado en reposo, rotación de claves y retención gobernada.
- Señal de activación: backup exportado o almacenado sin cifrado verificable.

### R002.7 — Exposición de documentos a proveedores de IA

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: la IA permanece desacoplada del dominio y no es fuente de verdad.
- Mitigación futura: política explícita de redacción, consentimiento y rutas permitidas por tipo documental.
- Señal de activación: envío de documentos sensibles a un proveedor sin política aprobada.

### R002.8 — Dependencia de terceros

- Probabilidad: Alta.
- Impacto: Alto.
- Mitigación actual: arquitectura modular y adaptadores.
- Mitigación futura: rutas alternativas, contratos de servicio y capacidad de sustitución.
- Señal de activación: bloqueo del sistema por caída o cambio unilateral del tercero.

### R002.9 — Ransomware

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: infraestructura local mínima y superficies reducidas.
- Mitigación futura: backups inmutables, segmentación, hardening y respuesta a incidentes.
- Señal de activación: cifrado de archivos, accesos anómalos o comportamiento extorsivo.

### R002.10 — Errores humanos

- Probabilidad: Alta.
- Impacto: Alto.
- Mitigación actual: confirmación humana para acciones sensibles y validaciones explícitas.
- Mitigación futura: mejores guardrails, UX preventiva y revisión de cambios críticos.
- Señal de activación: acciones irreversibles por error de operador o configuración.

### R002.11 — Falta de autenticación y autorización

- Probabilidad: Media.
- Impacto: Muy alto.
- Mitigación actual: endpoints con validaciones básicas y control local del entorno.
- Mitigación futura: autenticación formal, autorización granular y auditoría por identidad.
- Señal de activación: accesos sin identidad, permisos demasiado amplios o rutas abiertas por defecto.

### R002.12 — Ausencia de política de retención

- Probabilidad: Media.
- Impacto: Alto.
- Mitigación actual: conservación general de datos en PostgreSQL y trazabilidad de eventos.
- Mitigación futura: política documentada por tipo de dato, expiración y eliminación controlada.
- Señal de activación: crecimiento descontrolado, retención indefinida o eliminación no gobernada.

### R002.13 — Riesgo de supply chain

- Probabilidad: Media.
- Impacto: Alto.
- Mitigación actual: dependencias acotadas y contenedores base conocidos.
- Mitigación futura: pinning, escaneo de dependencias, revisión de actualizaciones y SBOM.
- Señal de activación: paquete comprometido, actualización inesperada o comportamiento anómalo en build/runtime.
