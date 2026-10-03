from __future__ import annotations

from pydantic import BaseModel

from .contracts import HtrRequest, HtrResult
from .jobs import HtrJob


class HtrQueueMessage(BaseModel):
    job: HtrJob
    request: HtrRequest


class HtrQueueResult(BaseModel):
    job: HtrJob
    result: HtrResult | None = None
