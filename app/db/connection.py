from collections.abc import AsyncIterator

from asyncpg import Connection

from app.core.postgres import db


async def get_connection() -> AsyncIterator[Connection]:
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        yield conn
