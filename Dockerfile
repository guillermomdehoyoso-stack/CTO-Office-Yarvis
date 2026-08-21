# syntax=docker/dockerfile:1

FROM node:20-alpine AS web-build

WORKDIR /build/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --ignore-scripts
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    YARVIS_API_HOST=0.0.0.0 \
    YARVIS_API_PORT=8080 \
    YARVIS_WEB_STATIC_ROOT=/app/web \
    YARVIS_WORKSPACE_REPOSITORY_ROOT=/workspace-repository \
    YARVIS_DOCUMENT_STORAGE_ROOT=/var/yarvis-documents

RUN apt-get update \
    && apt-get install --no-install-recommends -y libatomic1 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system yarvis \
    && useradd --system --gid yarvis --home-dir /app --shell /usr/sbin/nologin yarvis

WORKDIR /app
COPY apps/api/requirements.txt ./
RUN pip install --requirement requirements.txt
COPY apps/api/alembic.ini ./
COPY apps/api/migrations ./migrations
COPY apps/api/src ./src
COPY --from=web-build /build/web/dist ./web
COPY AGENTS.md /workspace-repository/AGENTS.md
COPY docs/development /workspace-repository/docs/development
COPY docs/engineering /workspace-repository/docs/engineering
COPY apps/api/workspaces /workspace-repository/apps/workspaces
RUN mkdir --parents /var/yarvis-documents \
    && chown --recursive yarvis:yarvis /app /workspace-repository /var/yarvis-documents

USER yarvis
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/health', timeout=3).read()"

CMD ["sh", "-c", "uvicorn yarvis_api.main:app --app-dir src --host 0.0.0.0 --port ${PORT:-8080}"]
