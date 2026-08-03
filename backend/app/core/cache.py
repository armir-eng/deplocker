from datetime import timedelta
from typing import Any

from redis.asyncio import ConnectionPool, Redis

from app.core.conf import settings


class RedisManager:
    def __init__(self) -> None:
        self.redis_pool = ConnectionPool(
            host=settings.REDIS_HOST,
            password=settings.REDIS_PASSWORD,
            port=settings.REDIS_PORT,
            max_connections=100,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        self.redis = Redis(connection_pool=self.redis_pool)

    async def ping(self) -> None:
        await self.redis.ping()  # type: ignore[misc]

    async def disconnect(self) -> None:
        await self.redis.close()

    async def get(self, key: str) -> Any:
        return await self.redis.get(key)

    async def set(self, key: str, value: str) -> None:
        await self.redis.set(key, value)

    async def json_get(self, key: str, path: str = "$") -> Any:
        return await self.redis.json().get(key, path)  # type: ignore[misc]

    async def json_set(self, key: str, value: Any, path: str = "$") -> None:
        await self.redis.json().set(name=key, path=path, obj=value)  # type: ignore[misc]

    async def json_delete(self, key: str, path: str = "$") -> None:
        await self.redis.json().delete(key=key, path=path)  # type: ignore[misc]

    async def arrappend(self, key: str, value: Any, path: str = "$") -> None:
        await self.redis.json().arrappend(key, path, value)  # type: ignore[misc]

    async def arrpop(self, key: str, value: Any, path: str = "$") -> None:
        json_array_content: list = await self.redis.json().get(key, path)  # type: ignore[misc]
        searching_value_index = json_array_content.index(value)
        await self.redis.json().arrpop(key, path, searching_value_index)  # type: ignore[misc]

    async def setex(
        self, session_id: str, expiry_time: int | timedelta, session_data: str
    ) -> None:
        await self.redis.setex(session_id, expiry_time, session_data)


redis = RedisManager()
