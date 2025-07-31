from typing import Any, List, Optional

import asyncpg

from marcus.observability.logging import get_logger

logger = get_logger(__name__)


class AsyncPGRepository:
    CONNECTION_POOL_NOT_INITIALIZED = "Connection pool not initialized."

    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10):
        """
        Initialize the AsyncPGRepository.
        Use this to set up connection pool parameters.
        Call connect() before using any database methods.
        """
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.pool.Pool] = None

    async def connect(self):
        """
        Establish the asyncpg connection pool.
        Must be called before any database operations.
        """
        self.pool = await asyncpg.create_pool(
            dsn=self.dsn, min_size=self.min_size, max_size=self.max_size
        )
        logger.info("Postgres connection pool created.")

    async def close(self):
        """
        Close the asyncpg connection pool.
        Call this when shutting down the application.
        """
        if self.pool:
            await self.pool.close()
            logger.info("Postgres connection pool closed.")

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Run a SELECT query and return all results as a list of records.
        Use for multi-row queries.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return await conn.fetch(query, *args)
        finally:
            await self.pool.release(conn)

    async def execute(self, query: str, *args) -> str:
        """
        Run an INSERT, UPDATE, or DELETE query.
        Returns command status string.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return await conn.execute(query, *args)
        finally:
            await self.pool.release(conn)

    async def fetch_single(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Run a SELECT query and return a single record (first row).
        Use for queries expecting one result.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return await conn.fetchrow(query, *args)
        finally:
            await self.pool.release(conn)

    async def fetch_value(self, query: str, *args) -> Any:
        """
        Run a SELECT query and return a single value (first column of first row).
        Use for scalar queries.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return await conn.fetchval(query, *args)
        finally:
            await self.pool.release(conn)

    async def acquire(self):
        """
        Acquire a raw connection from the pool.
        Use for advanced scenarios (manual transaction, bulk ops).
        Most users should use higher-level methods instead.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        return await self.pool.acquire()

    async def release(self, connection):
        """
        Release a raw connection back to the pool.
        Use only if you manually acquired a connection.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        await self.pool.release(connection)

    async def executemany(self, query: str, args_list):
        """
        Run a query with multiple sets of arguments (bulk insert/update).
        Use for batch operations.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return await conn.executemany(query, args_list)
        finally:
            await self.pool.release(conn)

    async def copy_from_table(self, table_name, source, *args, **kwargs):
        """
        Bulk load data into a table from a source (file, buffer).
        Use for efficient data import.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return await conn.copy_from_table(table_name, source, *args, **kwargs)
        finally:
            await self.pool.release(conn)

    async def copy_to_table(self, table_name, destination, *args, **kwargs):
        """
        Bulk export data from a table to a destination (file, buffer).
        Use for efficient data export.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return await conn.copy_to_table(table_name, destination, *args, **kwargs)
        finally:
            await self.pool.release(conn)

    async def transaction(self, *args, **kwargs):
        """
        Create a transaction context manager for advanced transaction control.
        Use for multi-step operations requiring atomicity.
        Most users should use higher-level methods unless custom transaction logic is needed.
        """
        if not self.pool:
            raise RuntimeError(self.CONNECTION_POOL_NOT_INITIALIZED)
        conn = await self.pool.acquire()
        try:
            return conn.transaction(*args, **kwargs)
        finally:
            await self.pool.release(conn)
