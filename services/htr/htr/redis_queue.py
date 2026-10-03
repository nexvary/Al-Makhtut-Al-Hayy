from __future__ import annotations

import json

from redis import Redis

from .worker_contract import HtrQueueMessage, HtrQueueResult


class RedisHtrQueue:
    def __init__(self, url: str, *, queue_name: str = "makhtut:htr") -> None:
        self.redis = Redis.from_url(url, decode_responses=True)
        self.queue_name = queue_name
        self.result_prefix = f"{queue_name}:result:"

    def enqueue(self, message: HtrQueueMessage) -> None:
        self.redis.rpush(self.queue_name, message.model_dump_json())

    def dequeue(self, timeout_seconds: int = 5) -> HtrQueueMessage | None:
        item = self.redis.blpop(self.queue_name, timeout=timeout_seconds)
        if item is None:
            return None
        _, payload = item
        return HtrQueueMessage.model_validate_json(payload)

    def store_result(self, result: HtrQueueResult, *, ttl_seconds: int = 86400) -> None:
        key = f"{self.result_prefix}{result.job.id}"
        self.redis.setex(key, ttl_seconds, result.model_dump_json())

    def get_result(self, job_id: str) -> HtrQueueResult | None:
        payload = self.redis.get(f"{self.result_prefix}{job_id}")
        return HtrQueueResult.model_validate_json(payload) if payload else None
