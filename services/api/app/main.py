import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .academy_routes import router as academy_router
from .account_routes import router as account_router
from .ai_lab_routes import router as ai_lab_router
from .editorial_routes import router as editorial_router
from .heritage_qa_routes import router as heritage_qa_router
from .heritage_routes import router as heritage_router
from .ingestion_routes import router as ingestion_router
from .knowledge_routes import router as knowledge_router
from .living_routes import router as living_router
from .logging_utils import RequestLogMiddleware, configure_logging
from .models import Manuscript
from .museum_routes import router as museum_router
from .ottoman_routes import router as ottoman_router
from .qa_routes import router as qa_router
from .ratelimit import RateLimitMiddleware
from .repository import repository
from .request_limits import MetadataSafetyMiddleware
from .scholarship_routes import router as scholarship_router
from .settings import settings, validate_production_settings
from .visual_index_routes import router as visual_index_router
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
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PATCH"],
                   allow_headers=["Authorization", "Content-Type"])
app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=app_settings.rate_limit_per_minute,
)
app.add_middleware(MetadataSafetyMiddleware)
app.include_router(account_router)
app.include_router(editorial_router)
app.include_router(ingestion_router)
app.include_router(knowledge_router)
app.include_router(qa_router)
app.include_router(scholarship_router)
app.include_router(visual_router)
app.include_router(visual_index_router)
app.include_router(living_router)
app.include_router(ai_lab_router)
app.include_router(ottoman_router)
app.include_router(academy_router)
app.include_router(heritage_router)
app.include_router(museum_router)
app.include_router(heritage_qa_router)


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
