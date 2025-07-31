import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from marcus.observability.metrics import (
    setup_opentelemetry_metrics,
    setup_instrumentation,
    cleanup_metrics,
)

class DummyDBRepo:
    def __init__(self, healthy=True):
        self.healthy = healthy
    async def fetch_value(self, query):
        if self.healthy:
            return 1
        raise Exception("DB not healthy")

class MetricsTestCase(unittest.TestCase):
    def test_health_metrics_update(self):
        # Covers metric update logic for /health endpoint
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_healthz_metrics_update_healthy(self):
        # Covers metric update logic for /healthz endpoint (healthy)
        self.app.state.db_repository = DummyDBRepo(healthy=True)
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["details"]["database"]["status"], "healthy")
        self.assertIsNone(data["details"]["database"]["error"])

    def test_healthz_metrics_update_unhealthy(self):
        # Covers metric update logic for /healthz endpoint (unhealthy)
        self.app.state.db_repository = DummyDBRepo(healthy=False)
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["details"]["database"]["status"], "unhealthy")
        self.assertIn("DB not healthy", data["details"]["database"]["error"])

    def test_healthz_metrics_update_no_db(self):
        # Covers metric update logic for /healthz endpoint (no db)
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["details"]["database"]["status"], "unhealthy")
        self.assertEqual(data["details"]["database"]["error"], "db_repository not initialized")

    def test_cleanup_metrics_shutdown(self):
        # Covers cleanup_metrics logic when meter_provider is set
        from marcus.observability.metrics import OpenTelemetryMetrics
        class DummyMeterProvider:
            def __init__(self):
                self.shutdown_called = False
            def shutdown(self):
                self.shutdown_called = True
        OpenTelemetryMetrics.meter_provider = DummyMeterProvider()
        cleanup_metrics()
        self.assertIsNone(OpenTelemetryMetrics.meter_provider)
    def setUp(self):
        from prometheus_client import CollectorRegistry
        self.registry = CollectorRegistry()
        self.app = FastAPI()
        setup_opentelemetry_metrics(self.app, registry=self.registry)
        setup_instrumentation(self.app)
        self.client = TestClient(self.app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_healthz_healthy(self):
        self.app.state.db_repository = DummyDBRepo(healthy=True)
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["details"]["database"]["status"], "healthy")
        self.assertIsNone(data["details"]["database"]["error"])

    def test_healthz_unhealthy(self):
        self.app.state.db_repository = DummyDBRepo(healthy=False)
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["details"]["database"]["status"], "unhealthy")
        self.assertIn("DB not healthy", data["details"]["database"]["error"])

    def test_healthz_no_db(self):
        # db_repository not set
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertEqual(data["details"]["database"]["status"], "unhealthy")
        self.assertEqual(data["details"]["database"]["error"], "db_repository not initialized")

    def test_cleanup_metrics(self):
        # Should not raise
        cleanup_metrics()
    
 