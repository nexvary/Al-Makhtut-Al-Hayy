from fastapi import FastAPI, HTTPException

from .editorial_routes import router as editorial_router
from .ingestion_routes import router as ingestion_router
from .knowledge_routes import router as knowledge_router
from .models import Manuscript
from .qa_routes import router as qa_router
from .repository import repository
from .visual_routes import router as visual_router

app = FastAPI(
    title="المخطوط الحي API",
    version="0.6.0",
    description="Source-traceable API for interactive historical Arabic manuscripts.",
)
app.include_router(editorial_router)
app.include_router(ingestion_router)
app.include_router(knowledge_router)
app.include_router(qa_router)
app.include_router(visual_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "al-makhtut-al-hayy-api"}


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
        "status": "foundation",
        "docs": "/docs",
    }
