from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-process fixed-window limiter.

    Production multi-replica deployments should switch the counter backend to Redis.
    """

    def __init__(self, app, *, requests_per_minute: int = 120) -> None:
        super().__init__(app)
        self.limit = max(requests_per_minute, 1)
        self._buckets: dict[tuple[str, int], int] = defaultdict(int)

    async def dispatch(self, request: Request, call_next):
        now = int(time.time())
        minute = now // 60
        client = request.client.host if request.client else "unknown"
        key = (client, minute)
        self._buckets[key] += 1
        if self._buckets[key] > self.limit:
            return JSONResponse(
                {"detail": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(60 - (now % 60))},
            )
        if len(self._buckets) > 10_000:
            self._buckets = defaultdict(
                int,
                {bucket: count for bucket, count in self._buckets.items() if bucket[1] >= minute - 1},
            )
        return await call_next(request)
