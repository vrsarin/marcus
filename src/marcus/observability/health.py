from typing import Optional

from opentelemetry import metrics
from prometheus_client import Counter

from .logging import get_logger

logger = get_logger(__name__)


class HealthMetrics:
    def __init__(self):
        self.health_check_counter: Optional[metrics.Counter] = None
        self.prom_health_check_counter: Optional[Counter] = None

    def setup(self, meter: Optional[metrics.Meter] = None, registry=None):
        if meter:
            self.health_check_counter = meter.create_counter(
                name="agent_registry_health_checks_total",
                description="Total number of health checks",
                unit="1",
            )
            logger.info("OpenTelemetry health metrics configured successfully")

        if registry is not None:
            self.prom_health_check_counter = Counter(
                "agent_registry_health_checks_total",
                "Total number of health checks",
                ["status"],
                registry=registry
            )
        else:
            self.prom_health_check_counter = Counter(
                "agent_registry_health_checks_total",
                "Total number of health checks",
                ["status"],
            )
        logger.info("Prometheus health metrics configured successfully")

    def record(self, status: str):
        if self.health_check_counter:
            self.health_check_counter.add(1, {"status": status})
        if self.prom_health_check_counter:
            self.prom_health_check_counter.labels(status=status).inc()


health_metrics = HealthMetrics()
