from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AgentKind(StrEnum):
    MACHINE = "machine"
    HUMAN = "human"
    IMPORT = "import"


class ProvenanceEvent(BaseModel):
    event_type: str
    manuscript_id: str
    page_id: str | None = None
    region_id: str | None = None
    agent_kind: AgentKind
    agent_id: str
    model_id: str | None = None
    source_uri: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
