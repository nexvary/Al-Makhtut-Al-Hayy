from fastapi import FastAPI, HTTPException

from .models import Manuscript
from .repository import repository

app = FastAPI(
    title="المخطوط الحي API",
    version="0.2.0",
    description="Source-traceable API for interactive historical Arabic manuscripts.",
)


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
