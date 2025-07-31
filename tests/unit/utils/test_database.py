import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from marcus.utils.database import AsyncPGRepository


class TestAsyncPGRepository(unittest.IsolatedAsyncioTestCase):
   
    def setUp(self):
        self.repo = AsyncPGRepository(dsn="postgresql://user:pass@localhost/db")
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock()
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock

    async def test_fetch(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.fetch = AsyncMock(return_value=[MagicMock()])
        result = await self.repo.fetch("SELECT * FROM test")
        self.assertIsInstance(result, list)
        self.repo.pool.acquire.assert_awaited_once()
        self.repo.pool.release.assert_awaited_once_with(conn)
        conn.fetch.assert_awaited_once_with("SELECT * FROM test")

    async def test_execute(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.execute = AsyncMock(return_value="INSERT 0 1")
        result = await self.repo.execute("INSERT INTO test VALUES (1)")
        self.assertEqual(result, "INSERT 0 1")
        conn.execute.assert_awaited_once_with("INSERT INTO test VALUES (1)")

    async def test_fetch_single(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.fetchrow = AsyncMock(return_value=MagicMock())
        result = await self.repo.fetch_single("SELECT * FROM test WHERE id=1")
        self.assertIsNotNone(result)
        conn.fetchrow.assert_awaited_once_with("SELECT * FROM test WHERE id=1")

    async def test_fetch_value(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.fetchval = AsyncMock(return_value=42)
        result = await self.repo.fetch_value("SELECT COUNT(*) FROM test")
        self.assertEqual(result, 42)
        conn.fetchval.assert_awaited_once_with("SELECT COUNT(*) FROM test")

    async def test_acquire_and_release(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        result = await self.repo.acquire()
        self.assertEqual(result, conn)
        await self.repo.release(conn)
        self.repo.pool.release.assert_awaited_once_with(conn)

    async def test_executemany(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.executemany = AsyncMock(return_value=None)
        result = await self.repo.executemany(
            "INSERT INTO test VALUES ($1)", [(1,), (2,)]
        )
        self.assertIsNone(result)
        conn.executemany.assert_awaited_once_with(
            "INSERT INTO test VALUES ($1)", [(1,), (2,)]
        )

    async def test_copy_from_table(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.copy_from_table = AsyncMock(return_value="done")
        result = await self.repo.copy_from_table("table", "source")
        self.assertEqual(result, "done")
        conn.copy_from_table.assert_awaited_once_with("table", "source")

    async def test_copy_to_table(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.copy_to_table = AsyncMock(return_value="done")
        result = await self.repo.copy_to_table("table", "dest")
        self.assertEqual(result, "done")
        conn.copy_to_table.assert_awaited_once_with("table", "dest")

    async def test_transaction(self):
        conn = AsyncMock()
        self.repo.pool.acquire = AsyncMock(return_value=conn)
        self.repo.pool.release = AsyncMock()
        conn.transaction = MagicMock(return_value="tx")
        result = await self.repo.transaction()
        self.assertEqual(result, "tx")
        conn.transaction.assert_called_once()

    async def test_pool_not_initialized(self):
        repo = AsyncPGRepository(dsn="postgresql://user:pass@localhost/db")
        with self.assertRaises(RuntimeError):
            await repo.fetch("query")
        with self.assertRaises(RuntimeError):
            await repo.execute("query")
        with self.assertRaises(RuntimeError):
            await repo.fetch_single("query")
        with self.assertRaises(RuntimeError):
            await repo.fetch_value("query")
        with self.assertRaises(RuntimeError):
            await repo.acquire()
        with self.assertRaises(RuntimeError):
            await repo.release(MagicMock())
        with self.assertRaises(RuntimeError):
            await repo.executemany("query", [(1,)])
        with self.assertRaises(RuntimeError):
            await repo.copy_from_table("table", "source")
        with self.assertRaises(RuntimeError):
            await repo.copy_to_table("table", "dest")
        with self.assertRaises(RuntimeError):
            await repo.transaction()

    @patch('marcus.utils.database.asyncpg')
    @patch('marcus.utils.database.logger')
    async def test_connect_and_close(self, mock_logger, mock_asyncpg):
        repo = AsyncPGRepository(dsn="postgresql://user:pass@localhost/db")
        pool_mock = MagicMock()
        pool_mock.close = AsyncMock()
        mock_asyncpg.create_pool = AsyncMock(return_value=pool_mock)
        await repo.connect()
        mock_asyncpg.create_pool.assert_awaited_once_with(dsn=repo.dsn, min_size=repo.min_size, max_size=repo.max_size)
        self.assertEqual(repo.pool, pool_mock)
        mock_logger.info.assert_any_call("Postgres connection pool created.")
        await repo.close()
        pool_mock.close.assert_awaited_once()
        mock_logger.info.assert_any_call("Postgres connection pool closed.")

    async def test_fetch_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.fetch = AsyncMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.fetch("SELECT * FROM test")
        pool_mock.release.assert_awaited_once_with(conn)

    async def test_execute_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.execute = AsyncMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.execute("INSERT INTO test VALUES (1)")
        pool_mock.release.assert_awaited_once_with(conn)

    async def test_fetch_single_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.fetchrow = AsyncMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.fetch_single("SELECT * FROM test WHERE id=1")
        pool_mock.release.assert_awaited_once_with(conn)

    async def test_fetch_value_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.fetchval = AsyncMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.fetch_value("SELECT COUNT(*) FROM test")
        pool_mock.release.assert_awaited_once_with(conn)

    async def test_executemany_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.executemany = AsyncMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.executemany("INSERT INTO test VALUES ($1)", [(1,)])
        pool_mock.release.assert_awaited_once_with(conn)

    async def test_copy_from_table_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.copy_from_table = AsyncMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.copy_from_table("table", "source")
        pool_mock.release.assert_awaited_once_with(conn)

    async def test_copy_to_table_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.copy_to_table = AsyncMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.copy_to_table("table", "dest")
        pool_mock.release.assert_awaited_once_with(conn)

    async def test_transaction_release_on_exception(self):
        conn = AsyncMock()
        pool_mock = MagicMock()
        pool_mock.acquire = AsyncMock(return_value=conn)
        pool_mock.release = AsyncMock()
        self.repo.pool = pool_mock
        conn.transaction = MagicMock(side_effect=Exception("fail"))
        with self.assertRaises(Exception):
            await self.repo.transaction()
        pool_mock.release.assert_awaited_once_with(conn)
