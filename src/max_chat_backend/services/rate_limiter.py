import logging
from dataclasses import dataclass

import redis

from max_chat_backend.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    is_allowed: bool
    current_count: int
    retry_after_seconds: int | None = None


class RedisRateLimiter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    def check(self, key: str, *, capacity: int | None = None, period_seconds: int | None = None) -> RateLimitResult:
        bucket_capacity = capacity or self.settings.rate_limiter_capacity
        bucket_period = period_seconds or self.settings.rate_limiter_period
        redis_key = f"rate_limit:{key}"

        try:
            current_count = int(self.client.incr(redis_key))
            if current_count == 1:
                self.client.expire(redis_key, bucket_period)
            ttl = self.client.ttl(redis_key)
            return RateLimitResult(
                is_allowed=current_count <= bucket_capacity,
                current_count=current_count,
                retry_after_seconds=max(ttl, 0),
            )
        except redis.RedisError:
            logger.exception("Rate limiter is unavailable; allowing request.")
            return RateLimitResult(is_allowed=True, current_count=0, retry_after_seconds=None)

    @staticmethod
    def user_key(max_user_id: int, action: str = "message") -> str:
        return f"user:{max_user_id}:{action}"

