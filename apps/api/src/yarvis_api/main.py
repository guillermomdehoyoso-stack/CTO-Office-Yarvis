from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from yarvis_api.config import get_settings
from yarvis_api.database import check_database_connection
from yarvis_api.api.routes import cases, checklists, evidence, intake, mission_control, organizations, people

settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organizations.router)
app.include_router(people.router)
app.include_router(cases.router)
app.include_router(intake.router)
app.include_router(evidence.router)
app.include_router(checklists.router)
app.include_router(mission_control.router)


@app.get("/health")
def health() -> dict[str, str]:
    try:
        check_database_connection(settings.database_url)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "degraded",
                "service": "yarvis-api",
                "database": "unavailable",
            },
        ) from exc

    return {"status": "ok", "service": "yarvis-api", "database": "ok"}
