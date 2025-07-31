import os
from contextlib import asynccontextmanager
from typing import List

from asyncpg import PostgresError
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from marcus.models import RankRequest, RankResult
from marcus.observability.metrics import setup_instrumentation
from marcus.settings import Constants
from marcus.utils.database import AsyncPGRepository
from marcus.utils.jwt import get_jwt_user_id_dep

from marcus.observability import (
    DEFAULT_METRICS_ENDPOINT,
    get_logger,
    setup_opentelemetry_metrics,
    setup_tracing,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    app.state.db_repository = AsyncPGRepository(dsn=Constants.db_url())
    setup_opentelemetry_metrics(app,service_name="marcus")
    setup_tracing(api)
    await app.state.db_repository.connect()
    yield
    await app.state.db_repository.close()


api = FastAPI(lifespan=lifespan_context)
setup_instrumentation(api)


@api.exception_handler(PostgresError)
async def postgres_exception_handler(request: Request, exc: PostgresError):
    return JSONResponse(
        status_code=500, content={"detail": f"Database error: {str(exc)}"}
    )


@api.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"detail": f"Internal server error: {str(exc)}"}
    )


@api.post("/rank", response_model=List[RankResult], tags=["Demo API"])
async def rank_folders(
    request: RankRequest,
    http_request: Request,
    user_id: str = Depends(get_jwt_user_id_dep),
):
    folder_path = request.folder_path
    factor = request.factor

    # Query entitlements from DB
    db_repo = http_request.app.state.db_repository
    try:
        entitlements = await db_repo.fetchval(
            "SELECT entitlements FROM ent_user_entitilements WHERE user_id = $1",
            user_id,
        )
        logger.info("User %s entitlements: %s", user_id, entitlements)
    except Exception as e:
        logger.error("DB entitlement query failed: %s", e)
        raise HTTPException(
            status_code=500, detail="Error querying user entitlements."
        ) from e

    if not os.path.isdir(folder_path):
        logger.error("Invalid folder path: %s", folder_path)
        raise HTTPException(status_code=400, detail="Invalid folder path.")

    try:
        folders = [
            f
            for f in os.listdir(folder_path)
            if os.path.isdir(os.path.join(folder_path, f))
        ]
    except Exception as e:
        logger.error("Error listing folders: %s", e)
        raise HTTPException(status_code=500, detail="Error reading folders.") from e

    results = []
    for folder in folders:
        score = 1.0
        reason = f"Ranked by factor '{factor}' (LLM integration needed)"
        results.append(RankResult(folder=folder, score=score, reason=reason))

    logger.info(
        "Ranked %d folders for factor '%s' (User: %s, Entitlements: %s)",
        len(results),
        factor,
        user_id,
        entitlements,
    )
    return results
