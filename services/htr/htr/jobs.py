from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class HtrJobState(StrEnum):
    QUEUED = "queued"
    FETCHING = "fetching"
    SEGMENTING = "segmenting"
    RECOGNIZING = "recognizing"
    SERIALIZING = "serializing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ALLOWED: dict[HtrJobState, set[HtrJobState]] = {
    HtrJobState.QUEUED: {HtrJobState.FETCHING, HtrJobState.CANCELLED},
    HtrJobState.FETCHING: {HtrJobState.SEGMENTING, HtrJobState.FAILED, HtrJobState.CANCELLED},
    HtrJobState.SEGMENTING: {HtrJobState.RECOGNIZING, HtrJobState.FAILED, HtrJobState.CANCELLED},
    HtrJobState.RECOGNIZING: {HtrJobState.SERIALIZING, HtrJobState.FAILED, HtrJobState.CANCELLED},
    HtrJobState.SERIALIZING: {HtrJobState.SUCCEEDED, HtrJobState.FAILED, HtrJobState.CANCELLED},
    HtrJobState.SUCCEEDED: set(),
    HtrJobState.FAILED: set(),
    HtrJobState.CANCELLED: set(),
}


class HtrJob(BaseModel):
    id: str
    manuscript_id: str
    page_id: str
    state: HtrJobState = HtrJobState.QUEUED
    model_id: str | None = None
    error: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    def transition(self, target: HtrJobState) -> "HtrJob":
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"Invalid HTR transition: {self.state} -> {target}")
        return self.model_copy(update={"state": target})
