# CTO Office / Yarvis

Base de conocimiento y plataforma inicial para el desarrollo de CTO Office y Yarvis, con enfoque en la amplificación del fundador, la gestión operativa por Casos y el Foundation Sprint.

## Estructura

- docs/vision: manifiesto, sistema operativo y visión de largo plazo.
- docs/business: business blueprint y modelo de negocio.
- docs/architecture: blueprint técnico, modelo de dominio y arquitectura del MVP.
- docs/product: scope, backlog, sprint y criterios de aceptación.
- docs/decisions: decisiones arquitectónicas registradas.
- docs/build-log: historial de construcción.
- docs/engineering: estándares y prácticas de ingeniería.
- docs/templates: plantillas reutilizables.
- docs/standards: estándares de documentación.

## Principio central

Modelar primero el dominio, después la arquitectura y finalmente el código.

## Foundation Sprint - Bloque 1

Primer incremento tecnico ejecutable:

- API FastAPI;
- endpoint `GET /health`;
- comprobacion de conexion con PostgreSQL;
- configuracion por variables de entorno;
- Docker Compose para API y PostgreSQL;
- prueba automatizada del endpoint de salud.

MinIO queda deliberadamente fuera del Bloque 1. El almacenamiento documental pertenece a un incremento posterior; este bloque valida solamente API, salud, configuracion y PostgreSQL.

### Requisitos

- Docker
- Docker Compose

### Configuracion

Copiar `.env.example` a `.env` si se desea ajustar la configuracion local. Docker Compose tambien funciona con los valores por defecto definidos en `docker-compose.yml`.

Variables principales:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`

### Ejecutar

```bash
docker compose up --build
```

Verificar salud:

```bash
curl http://localhost:8000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "yarvis-api",
  "database": "ok"
}
```

### Migraciones

La API no crea tablas automáticamente. Con los servicios arriba, aplicar el esquema versionado:

```bash
docker compose exec api alembic upgrade head
```

### Pruebas

```bash
docker compose run --rm api sh -c "pip install -r requirements-dev.txt && pytest"
```

Las pruebas usan la base separada `yarvis_test` dentro del mismo servicio PostgreSQL. Pytest la crea y trunca entre pruebas; nunca usa ni borra el volumen o los datos de `yarvis`.

### Datos de demostración opcionales

Después de aplicar migraciones, crear Energía Fotónica, Juan Manuel y su Caso demostrativo (el comando es idempotente):

```bash
docker compose exec api python -m yarvis_api.seed
```

### Persistencia y detención

Para detener los servicios sin eliminar los datos de PostgreSQL:

```bash
docker compose down
docker compose up -d
docker compose exec api alembic upgrade head
```

El volumen `pgdata` se conserva. Se puede comprobar la persistencia con `GET /organizations`, `GET /people` o `GET /cases`.

### Ingreso manual, evidencia y bitácora

Tras aplicar migraciones, se puede registrar texto recibido y asociarlo a un Caso:

```bash
curl -X POST http://localhost:8000/intake -H "Content-Type: application/json" -d '{"source_type":"manual_text","content_type":"text/plain","text_content":"Cliente solicitó cambio de servicio"}'
curl -X POST http://localhost:8000/intake/{intake_id}/link-case/{case_id}
```

Registrar evidencia sin almacenar archivos binarios y consultar la bitácora inmutable:

```bash
curl -X POST http://localhost:8000/cases/{case_id}/evidence -H "Content-Type: application/json" -d '{"evidence_type":"photo","title":"Fotografías de preparación"}'
curl http://localhost:8000/cases/{case_id}/events
```

El comando de pruebas indicado arriba cubre también ingreso, evidencia y eventos sobre PostgreSQL.

### Catálogos y checklists configurables

Aplicar la migración y cargar los catálogos idempotentes:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python -m yarvis_api.catalogs
```

Crear un Caso con `case_type_id` obtenido de `GET /case-types`, crear su checklist y consultar su avance:

```bash
curl -X POST http://localhost:8000/cases/{case_id}/checklists
curl http://localhost:8000/case-checklists/{case_checklist_id}
```

La clasificación manual se crea en `POST /intake/{intake_id}/classifications` y se confirma en `POST /intake-classifications/{classification_id}/confirm`. Un requisito se recibe con `POST /case-checklists/{id}/requirements/{requirement_id}/fulfill` y se valida en `POST /requirement-fulfillments/{id}/validate`.
