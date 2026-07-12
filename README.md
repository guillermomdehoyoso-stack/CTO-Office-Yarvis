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

### Pruebas

```bash
docker compose run --rm api sh -c "pip install -r requirements-dev.txt && pytest"
```
