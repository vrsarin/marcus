import asyncpg
import logging
from typing import Any, List, Optional

logger = logging.getLogger("db_repository")


class AsyncPGRepository:
    CONNECTION_POOL_NOT_INITIALIZED = "Connection pool not initialized."

    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=self.min_size, max_size=self.max_size)
            logger.info("Postgres connection pool created.")
        except Exception as e:
            logger.error("Failed to create connection pool: %s", e)
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Postgres connection pool closed.")

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:

        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            logger.error("Error executing fetch: %s", e)
            raise

    async def execute(self, query: str, *args) -> str:
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error("Error executing query: %s", e)
            raise

    async def fetch_single(self, query: str, *args) -> Optional[asyncpg.Record]:
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except Exception as e:
            logger.error("Error executing fetchrow: %s", e)
            raise

    async def fetch_value(self, query: str, *args) -> Any:
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except Exception as e:
            logger.error("Error executing fetchval: %s", e)
            raise
