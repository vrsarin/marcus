import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from asyncpg import PostgresError
from marcus.utils.database import AsyncPGRepository
from marcus.models import RankRequest, RankResult
import marcus.main as main


class TestMain(unittest.IsolatedAsyncioTestCase):
    async def test_lifespan_context(self):
        app = MagicMock()
        repo_mock = MagicMock()
        repo_mock.connect = AsyncMock()
        repo_mock.close = AsyncMock()
        with patch("marcus.main.AsyncPGRepository", return_value=repo_mock):
            async with main.lifespan_context(app):
                repo_mock.connect.assert_awaited_once()
            repo_mock.close.assert_awaited_once()
            self.assertIs(app.state.db_repository, repo_mock)

    async def test_postgres_exception_handler(self):
        request = MagicMock(spec=Request)
        exc = PostgresError("fail")
        resp = await main.postgres_exception_handler(request, exc)
        self.assertIsInstance(resp, JSONResponse)
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Database error", bytes(resp.body).decode())

    async def test_generic_exception_handler(self):
        request = MagicMock(spec=Request)
        exc = Exception("fail")
        resp = await main.generic_exception_handler(request, exc)
        self.assertIsInstance(resp, JSONResponse)
        self.assertEqual(resp.status_code, 500)
        self.assertIn("Internal server error", bytes(resp.body).decode())

    async def test_health_ok(self):
        request = MagicMock(spec=Request)
        db_repo = MagicMock(spec=AsyncPGRepository)
        db_repo.fetch_value = AsyncMock(return_value=1)
        request.app.state.db_repository = db_repo
        with patch("marcus.main.logger") as logger_mock:
            result = await main.health(request)
            self.assertEqual(result, {"status": "ok"})
            db_repo.fetch_value.assert_awaited_once_with("SELECT 1")
            logger_mock.error.assert_not_called()

    async def test_health_db_error(self):
        request = MagicMock(spec=Request)
        db_repo = MagicMock(spec=AsyncPGRepository)
        db_repo.fetch_value = AsyncMock(side_effect=PostgresError("fail"))
        request.app.state.db_repository = db_repo
        with patch("marcus.main.logger") as logger_mock:
            result = await main.health(request)
            self.assertEqual(result["status"], "error")
            self.assertIn("fail", result["details"])
            logger_mock.error.assert_called()

    async def test_rank_folders_success(self):
        request_obj = MagicMock(spec=RankRequest)
        request_obj.folder_path = "/tmp"
        request_obj.factor = "test"
        http_request = MagicMock(spec=Request)
        db_repo = MagicMock(spec=AsyncPGRepository)
        db_repo.fetchval = AsyncMock(return_value="entitlements")
        http_request.app.state.db_repository = db_repo
        user_id = "user1"
        with (
            patch("marcus.main.logger") as logger_mock,
            patch("os.path.isdir", return_value=True),
            patch("os.listdir", return_value=["a", "b"]),
            patch("os.path.isdir", side_effect=lambda p: True),
        ):
            results = await main.rank_folders(request_obj, http_request, user_id)
            self.assertIsInstance(results, list)
            self.assertTrue(all(isinstance(r, RankResult) for r in results))
            logger_mock.info.assert_called()

    async def test_rank_folders_invalid_folder(self):
        request_obj = MagicMock(spec=RankRequest)
        request_obj.folder_path = "/tmp"
        request_obj.factor = "test"
        http_request = MagicMock(spec=Request)
        db_repo = MagicMock(spec=AsyncPGRepository)
        db_repo.fetchval = AsyncMock(return_value="entitlements")
        http_request.app.state.db_repository = db_repo
        user_id = "user1"
        with (
            patch("marcus.main.logger") as logger_mock,
            patch("os.path.isdir", return_value=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await main.rank_folders(request_obj, http_request, user_id)
            self.assertEqual(ctx.exception.status_code, 400)
            logger_mock.error.assert_called()

    async def test_rank_folders_db_error(self):
        request_obj = MagicMock(spec=RankRequest)
        request_obj.folder_path = "/tmp"
        request_obj.factor = "test"
        http_request = MagicMock(spec=Request)
        db_repo = MagicMock(spec=AsyncPGRepository)
        db_repo.fetchval = AsyncMock(side_effect=Exception("dbfail"))
        http_request.app.state.db_repository = db_repo
        user_id = "user1"
        with (
            patch("marcus.main.logger") as logger_mock,
            patch("os.path.isdir", return_value=True),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await main.rank_folders(request_obj, http_request, user_id)
            self.assertEqual(ctx.exception.status_code, 500)
            logger_mock.error.assert_called()

    async def test_rank_folders_listdir_error(self):
        request_obj = MagicMock(spec=RankRequest)
        request_obj.folder_path = "/tmp"
        request_obj.factor = "test"
        http_request = MagicMock(spec=Request)
        db_repo = MagicMock(spec=AsyncPGRepository)
        db_repo.fetchval = AsyncMock(return_value="entitlements")
        http_request.app.state.db_repository = db_repo
        user_id = "user1"
        with (
            patch("marcus.main.logger") as logger_mock,
            patch("os.path.isdir", return_value=True),
            patch("os.listdir", side_effect=Exception("fail")),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await main.rank_folders(request_obj, http_request, user_id)
            self.assertEqual(ctx.exception.status_code, 500)
            logger_mock.error.assert_called()
