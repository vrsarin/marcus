
import logging
import os
from contextlib import asynccontextmanager
from typing import List


from asyncpg import PostgresError
from fastapi import FastAPI, HTTPException, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from marcus.models import RankResult, RankRequest
from marcus.settings import Settings
from marcus.db_repository import AsyncPGRepository
from marcus.jwt_utils import get_user_id_from_jwt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_ranker")


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    app.state.settings = Settings()

    app.state.db_repository = AsyncPGRepository(
        dsn=app.state.settings.DATABASE_URL
    )
    await app.state.db_repository.connect()
    yield
    await app.state.db_repository.close()


api = FastAPI(lifespan=lifespan_context)

# Set up OpenTelemetry tracing
provider = TracerProvider()
trace.set_tracer_provider(provider)
otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)
FastAPIInstrumentor.instrument_app(api)


@api.post("/rank", response_model=List[RankResult])
async def rank_folders(request: RankRequest, http_request: Request):
    folder_path = request.folder_path
    factor = request.factor

    # Extract user_id from JWT token
    try:
        user_id = get_user_id_from_jwt(http_request)
    except HTTPException as e:
        logger.error("JWT extraction failed: %s", e.detail)
        raise

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
        raise HTTPException(
            status_code=500, detail="Error reading folders.") from e

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


@api.get("/health")
async def health(http_request: Request):
    db_repo: AsyncPGRepository = http_request.app.state.db_repository
    try:
        # Simple query to check DB connection
        await db_repo.fetch_value("SELECT 1")
        return {"status": "ok"}
    except PostgresError as e:
        logger.error("Health check failed: %s", e)
        return {"status": "error", "details": str(e)}
