import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .editorial_routes import router as editorial_router
from .ingestion_routes import router as ingestion_router
from .knowledge_routes import router as knowledge_router
from .living_routes import router as living_router
from .logging_utils import RequestLogMiddleware, configure_logging
from .models import Manuscript
from .qa_routes import router as qa_router
from .ratelimit import RateLimitMiddleware
from .repository import repository
from .scholarship_routes import router as scholarship_router
from .settings import settings, validate_production_settings
from .visual_routes import router as visual_router

app_settings = settings()
validate_production_settings(app_settings)
configure_logging()

app = FastAPI(
    title="المخطوط الحي API",
    version="0.1.0-rc1",
    description="Source-traceable API for interactive historical Arabic manuscripts.",
)
origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                   allow_headers=["Authorization", "Content-Type"])
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=app_settings.rate_limit_per_minute,
)
app.include_router(editorial_router)
app.include_router(ingestion_router)
app.include_router(knowledge_router)
app.include_router(qa_router)
app.include_router(scholarship_router)
app.include_router(visual_router)
app.include_router(living_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "al-makhtut-al-hayy-api"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/api/v1/manuscripts", response_model=list[Manuscript])
def list_manuscripts() -> list[Manuscript]:
    return repository.list()


@app.get("/api/v1/manuscripts/{manuscript_id}", response_model=Manuscript)
def get_manuscript(manuscript_id: str) -> Manuscript:
    manuscript = repository.get(manuscript_id)
    if manuscript is None:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return manuscript


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "المخطوط الحي — Living Manuscript",
        "status": "release-candidate",
        "docs": "/docs",
    }
