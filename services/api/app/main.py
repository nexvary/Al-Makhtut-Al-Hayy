from fastapi import FastAPI

from .models import Manuscript

app = FastAPI(
    title="المخطوط الحي API",
    version="0.1.0",
    description="Source-traceable API for interactive historical Arabic manuscripts.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "al-makhtut-al-hayy-api"}


@app.get("/api/v1/manuscripts", response_model=list[Manuscript])
def list_manuscripts() -> list[Manuscript]:
    # Persistence is intentionally deferred until the provenance/data model is stabilized.
    return []


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "المخطوط الحي — Living Manuscript",
        "status": "foundation",
        "docs": "/docs",
    }
