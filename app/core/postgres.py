import asyncio

from asyncpg import Pool, create_pool

from app.core.config import settings


class Database:
    _instance: "Database | None" = None
    _pool: Pool | None
    _lock: asyncio.Lock

    def __new__(cls) -> "Database":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._pool = None
            instance._lock = asyncio.Lock()
            cls._instance = instance
        return cls._instance

    async def get_pool(self) -> Pool:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = await create_pool(
                        host=settings.postgres_host,
                        port=settings.postgres_port,
                        user=settings.postgres_user,
                        password=settings.postgres_pass,
                        database=settings.postgres_db,
                    )
        return self._pool


db = Database()
