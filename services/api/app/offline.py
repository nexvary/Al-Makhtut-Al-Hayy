from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from .models import Manuscript


class OfflinePack(BaseModel):
    format: str = "al-makhtut-offline-pack/v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    manuscript: Manuscript
    includes_images: bool = False
    source_notice: str = (
        "Images are excluded by default. Cache or redistribute source images only when rights permit."
    )


def make_offline_pack(manuscript: Manuscript) -> OfflinePack:
    return OfflinePack(manuscript=manuscript)
