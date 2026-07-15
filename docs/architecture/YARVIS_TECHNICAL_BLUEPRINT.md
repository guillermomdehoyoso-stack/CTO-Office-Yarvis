# Yarvis Technical Blueprint

## Referencia superior
- El documento [Yarvis Operating Model v1.0](YARVIS_OPERATING_MODEL.md) es la autoridad arquitectónica de mayor nivel para Yarvis.
- Los ADR específicos siguen siendo vinculantes cuando no contradicen ese Operating Model.

## 1. Objetivos técnicos
- Implementar un monolito modular para el Foundation Sprint.
- Soportar el flujo de recepción y avance de Casos para Expediente CFE residencial y Alta NetPay.
- Mantener auditoría, contexto y trazabilidad desde el inicio.

---

## 2. Restricciones
- Sin microservicios.
- Sin Kubernetes.
- Sin Kafka ni RabbitMQ.
- Sin modelos locales ni agentes autónomos.
- Sin integraciones reales con sistemas externos en la primera iteración.

---

## 3. Arquitectura de CTO Office
CTO Office proporciona los servicios compartidos: identidad, almacenamiento, eventos, auditoría, integración y observabilidad.

---

## 4. Arquitectura de Yarvis Core
Yarvis Core se implementa como una capa operativa sobre CTO Office con módulos internos para:
- organizaciones;
- personas;
- relaciones;
- casos;
- tipos de Caso;
- documentos;
- checklists;
- acciones;
- dependencias;
- eventos;
- auditoría;
- IA desacoplada.

La evolución futura de identidad operativa queda alineada con ADR-008 y con [IDENTITY_RESOLUTION.md](IDENTITY_RESOLUTION.md), incluyendo el uso de Asset como concepto general futuro cuando existan más de un dominio que requiera administración común de activos.

---

## 5. Monolito modular inicial
Se usará un monolito modular con capas bien delimitadas:
- API
- dominio
- persistencia
- infraestructura
- interfaz mínima

---

## 6. Límites de módulos
- El dominio no depende de web, IA ni almacenamiento documental concreto.
- El almacenamiento documental se abstrae mediante una interfaz.
- Las integraciones se mantienen como adaptadores externos.

---

## 7. Modelo de datos
El modelo de dominio se persistirá en PostgreSQL con migraciones Alembic. El núcleo inicial incluye organizaciones, personas, Casos, documentos, checklist y eventos.

---

## 8. Modelo de eventos
Cada cambio relevante debe emitir eventos auditable como:
- case.created
- document.received
- checklist.requirement.completed
- case.stage.changed
- next.action.created

---

## 9. Gestión documental
Los documentos se almacenan de forma persistente y se asocian a organización, actor, Caso, expediente, requisito y etapa.

---

## 10. Almacenamiento
Se recomienda MinIO como almacenamiento documental. Como alternativa inicial, se puede usar un adaptador local abstracto.

---

## 11. Máquina de estados
Se implementará una máquina simple configurable por tipo de Caso con estados y transiciones que validen precondiciones y generen eventos.

---

## 12. Checklists configurables
Cada tipo de Caso tendrá un checklist configurable y reglas de cumplimiento específicas.

---

## 13. Acciones y dependencias
Yarvis debe generar y actualizar acciones, compromisos y dependencias a partir del estado del Caso y los requisitos.

---

## 14. Auditoría
Todo cambio relevante debe registrarse con usuario o agente, acción, estado anterior, estado nuevo, origen y correlación.

---

## 15. Identidad y permisos
Se soportarán roles básicos, permisos por módulo y control de acceso a documentos y Casos.

---

## 16. Proveedores de inteligencia artificial desacoplados
La IA se implementará mediante un adaptador con interface simple que devuelva resultado, confianza, evidencia y necesidad de confirmación.

---

## 17. Extracción y clasificación documental
En el Foundation Sprint se priorizará la clasificación manual o sugerida, no reconocimiento avanzado.

---

## 18. Confirmación humana
Las acciones sensibles requieren confirmación explícita antes de ejecutarse.

---

## 19. Integraciones
Se crearán adaptadores futuros desacoplados; en el Sprint inicial se expondrá únicamente la capa de entrada manual y la lógica de asociación.

### SupplierCatalogConnector futuro
`SupplierCatalogConnector` será una interfaz futura para consultar tiendas autenticadas de proveedores sin acoplar el dominio a un proveedor específico ni implementar automatización de navegador en el Foundation Sprint.

Conceptualmente deberá soportar:
- autenticar;
- buscar productos;
- consultar disponibilidad;
- consultar precio;
- descargar documentos;
- registrar fecha y evidencia;
- cerrar o renovar sesión.

La interfaz deberá conservar evidencia suficiente para auditoría, comparación de costos y trazabilidad de decisiones de compra, sin ejecutar compras automáticas.

---

## 20. Despliegue mediante Docker Compose
Se planea un entorno con api, postgres y minio. El frontend mínimo puede integrarse después.

---

## 21. Pruebas
Se cubrirán pruebas unitarias y de integración básicas para ingreso, asociación, checklist y estado.

---

## 22. Observabilidad mínima
Logs estructurados, trazas de eventos y errores con contexto.

---

## 23. Seguridad
- secretos en variables de entorno;
- validación de entrada;
- permisos por rol;
- auditoría de acciones sensibles.

Para futuras consultas autenticadas a catálogos de proveedores:
- ninguna credencial debe almacenarse en Git;
- los secretos deben almacenarse en una bóveda;
- las sesiones autenticadas deben cifrarse;
- el acceso inicial debe ser de solo lectura;
- ninguna compra debe ejecutarse sin aprobación humana;
- todo acceso debe quedar auditado;
- el diseño debe tolerar verificación en dos pasos;
- se deben respetar términos de uso y límites del proveedor.

---

## 24. Respaldo
Se usará volumen persistente para PostgreSQL y almacenamiento documental, con restauración reproducible desde Docker Compose.

---

## 25. Estrategia de migraciones
Alembic para aplicar cambios de esquema de forma controlada.

---

## 26. Manejo de errores
Errores de validación, almacenamiento, reglas de negocio y correlación de eventos deben ser explícitos.

---

## 27. Evolución hacia conectores de WhatsApp
Se diseñará el flujo para permitir integración futura sin acoplar la lógica del dominio a WhatsApp.

---

## 28. Criterios para introducir colas, caché o servicios adicionales
Solo si aparecen cuellos de botella reales o necesidad de escalabilidad demostrada.

---

## 29. Alcance del Foundation Sprint
- Inbox manual.
- Registro de ingreso.
- Clasificación sugerida y confirmación.
- Casos CFE y NetPay.
- Checklist y avance.
- Siguiente acción y auditoría.

---

## 30. Fuera de alcance
- WhatsApp real.
- OpenSolar.
- Salesforce.
- Mifiel.
- Bancos.
- Automatización de navegador para tiendas de proveedores.
- Compras automáticas a proveedores.
- Modelos locales.
- Agentes autónomos.
- Aplicación móvil nativa.
