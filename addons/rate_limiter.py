# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Per-IP / per-endpoint token-bucket rate limiter (LAN-safe).

Prevents accidental tight loops without blocking normal operator usage.
"""

import time
from collections import defaultdict
from typing import Dict

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from addons.config_ext import get_config


class _TokenBucket:
    __slots__ = ("capacity", "tokens", "refill_rate", "last_refill")

    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        cfg = get_config()
        rpm = cfg.get("rate_limit_per_minute", 120)
        self._cap = float(rpm)
        self._rate = float(rpm) / 60.0
        self._buckets: Dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(capacity=self._cap, refill_rate=self._rate)
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        bucket = self._buckets[key]
        if not bucket.consume():
            raise HTTPException(status_code=429, detail="Rate limit exceeded â€” slow down")
        return await call_next(request)

