from __future__ import annotations

import json
from datetime import UTC, datetime
from difflib import ndiff
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from .legacy_store import LegacyRecordStore
from .models import TextLayerKind


class ReviewState(StrEnum):
    MACHINE = "machine"
    DRAFT = "draft"
    VERIFIED = "verified"
    REJECTED = "rejected"


class EditorialRole(StrEnum):
    VIEWER = "viewer"
    TRANSCRIBER = "transcriber"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class TextRevision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    manuscript_id: str
    page_id: str
    region_id: str
    layer_kind: TextLayerKind
    text: str
    state: ReviewState
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parent_revision_id: str | None = None
    note: str | None = None


class AuditEntry(BaseModel):
    action: str
    actor_id: str
    manuscript_id: str
    page_id: str
    region_id: str | None = None
    revision_id: str | None = None
    at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EditorialStore:
    def __init__(self, path: Path | None = None):
        self.store = LegacyRecordStore(path)

    @staticmethod
    def _key(manuscript_id: str, page_id: str, region_id: str):
        return json.dumps([manuscript_id,page_id,region_id])

    def add_revision(self, revision: TextRevision) -> TextRevision:
        if revision.layer_kind == TextLayerKind.HTR_RAW and revision.state != ReviewState.MACHINE:
            raise ValueError("HTR remains machine; review creates a different transcription layer")
        audit = AuditEntry(action="revision.created",actor_id=revision.created_by,
                           manuscript_id=revision.manuscript_id,page_id=revision.page_id,
                           region_id=revision.region_id,revision_id=revision.id)
        self.store.editorial_append(self._key(revision.manuscript_id,revision.page_id,revision.region_id),
                                    revision.id,revision.parent_revision_id,revision.model_dump_json(),audit.model_dump_json())
        return revision

    def history(self, manuscript_id: str, page_id: str, region_id: str) -> list[TextRevision]:
        return [TextRevision.model_validate_json(row) for row in self.store.editorial_history(self._key(manuscript_id,page_id,region_id))]

    def audit_log(self) -> list[AuditEntry]:
        return [AuditEntry.model_validate_json(row) for row in self.store.editorial_audit()]


editorial_store = EditorialStore()


def revision_diff(old: str, new: str) -> list[str]:
    return list(ndiff(old.split(), new.split()))


def confidence_bucket(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence < 0.60:
        return "critical"
    if confidence < 0.80:
        return "review"
    if confidence < 0.93:
        return "check"
    return "high"


def can_verify(role: EditorialRole) -> bool:
    return role in {EditorialRole.REVIEWER, EditorialRole.ADMIN}
