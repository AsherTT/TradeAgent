"""Cross-worker SEC request admission through the existing Redis service."""

import asyncio

from redis.asyncio import Redis
from redis.exceptions import RedisError

from backend.app.financials.sec import SecFinancialError


class RedisSecRequestLimiter:
    def __init__(self, redis_url: str) -> None:
        self._url = redis_url

    async def __call__(self) -> None:
        client = Redis.from_url(self._url, socket_connect_timeout=2, socket_timeout=2)
        try:
            async with asyncio.timeout(3):
                for _ in range(60):
                    if await client.set("tradeagent:sec:request-slot", "1", nx=True, px=250):
                        return
                    await asyncio.sleep(0.05)
                raise SecFinancialError("SEC shared request limiter busy")
        except (RedisError, TimeoutError):
            raise SecFinancialError("SEC shared request limiter unavailable") from None
        finally:
            await client.aclose()
