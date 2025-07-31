from typing import Optional

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import APIRouter, FastAPI, Request

from .health import health_metrics
from .logging import get_logger

logger = get_logger(__name__)

DEFAULT_METRICS_ENDPOINT = "/metrics"

class OpenTelemetryMetrics:
    # Metrics Globals
    meter: Optional[metrics.Meter] = None
    meter_provider: Optional[MeterProvider] = None
    instrumentator: Optional[Instrumentator] = None

# OpenTelemetery Metrics
health_check_counter = None

# Prometheus Metrics
prom_health_check_counter: Optional[Counter] = None
health_status_gauge: Optional[Gauge] = None

def setup_instrumentation(app:FastAPI,metric_endpoint: str = "/metrics"):
    OpenTelemetryMetrics.instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        # Ignore environment variable to always instrument metrics endpoint
        should_respect_env_var=False,
        # Disable in-progress request metric to avoid duplicate registration issues
        should_instrument_requests_inprogress=False,
        excluded_handlers=[metric_endpoint],
        env_var_name="ENABLE_METRICS",
        inprogress_name="agent_registry_inprogress",
        inprogress_labels=True,
    )
    OpenTelemetryMetrics.instrumentator.instrument(app).expose(app, endpoint=metric_endpoint,tags=["System"])

def setup_opentelemetry_metrics(app: FastAPI, 
    service_name: str = "agent-registry", service_version: str = "1.0.0",
    registry=None
):
    global health_check_counter, prom_health_check_counter, health_status_gauge

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    prometheus_reader = PrometheusMetricReader()
    OpenTelemetryMetrics.meter_provider = MeterProvider(
        resource=resource, metric_readers=[prometheus_reader]
    )
    metrics.set_meter_provider(OpenTelemetryMetrics.meter_provider)
    OpenTelemetryMetrics.meter = metrics.get_meter(__name__)

    # OpenTelemetry
    health_check_counter = OpenTelemetryMetrics.meter.create_counter(
        "api_health_checks_total",
        description="Total number of health checks",
        unit="1",
    )

    # Prometheus
    if registry is not None:
        prom_health_check_counter = Counter(
            "api_health_checks_total",
            "Total number of health checks",
            ["status"],
            registry=registry
        )
        health_status_gauge = Gauge(
            "api_health_status",
            "Service health status (1=healthy, 0=unhealthy)",
            [],
            registry=registry
        )
    else:
        prom_health_check_counter = Counter(
            "api_health_checks_total",
            "Total number of health checks",
            ["status"],
        )
        health_status_gauge = Gauge(
            "api_health_status",
            "Service health status (1=healthy, 0=unhealthy)",
            [],
        )


    router = APIRouter()

    @router.get("/health", tags=["System"])
    async def health_check():
        if health_status_gauge:
            # No labels for health_status_gauge, set value directly
            health_status_gauge.set(1)
        if health_check_counter:
            health_check_counter.add(1, {"status": "ok"})
        if prom_health_check_counter:
            prom_health_check_counter.labels(status="ok").inc()
        return {"status": "ok"}



    @router.get("/healthz", tags=["System"])
    async def readiness_check(request: Request):
        # Component checks
        details = {}
        ready = True

        # DB connectivity check
        db_repo = getattr(request.app.state, "db_repository", None)
        db_status = "unknown"
        db_error = None
        if db_repo:
            try:
                await db_repo.fetch_value("SELECT 1")
                db_status = "healthy"
            except Exception as e:
                db_status = "unhealthy"
                db_error = str(e)
                logger.error("Readiness DB check failed: %s", e)
        else:
            db_status = "unhealthy"
            db_error = "db_repository not initialized"

        details["database"] = {
            "status": db_status,
            "error": db_error,
        }
        if db_status != "healthy":
            ready = False

        # Add more component checks here as needed

        # Set metrics
        if health_status_gauge:
            health_status_gauge.set(1 if ready else 0)
        if health_check_counter:
            health_check_counter.add(1, {"status": "healthy" if ready else "unhealthy"})
        if prom_health_check_counter:
            prom_health_check_counter.labels(status="healthy" if ready else "unhealthy").inc()

        return {
            "status": "healthy" if ready else "unhealthy",
            "details": details
        }

    app.include_router(router)
    logger.info("OpenTelemetry metrics configured successfully")
    health_metrics.setup(OpenTelemetryMetrics.meter, registry=registry)

def cleanup_metrics():
    """Gracefully cleanup metrics during service shutdown"""
    logger.info("Starting metrics cleanup...")

    # Clear OpenTelemetry metrics
    if OpenTelemetryMetrics.meter_provider:
        OpenTelemetryMetrics.meter_provider.shutdown()
        logger.info("OpenTelemetry meter provider shutdown complete")

    # Reset OpenTelemetry globals
    OpenTelemetryMetrics.meter_provider = None

    logger.info("Metrics cleanup completed successfully")