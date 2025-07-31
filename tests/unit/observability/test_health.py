
import unittest
from unittest.mock import MagicMock, patch
from marcus.observability.health import HealthMetrics

class TestHealthMetrics(unittest.TestCase):

    def test_init(self):
        hm = HealthMetrics()
        self.assertIsNone(hm.health_check_counter)
        self.assertIsNone(hm.prom_health_check_counter)

    @patch('marcus.observability.health.Counter')
    def test_setup_with_meter(self, mock_prom_counter):
        mock_meter = MagicMock()
        mock_counter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter
        mock_prom = MagicMock()
        mock_prom_counter.return_value = mock_prom

        hm = HealthMetrics()
        hm.setup(meter=mock_meter)
        self.assertEqual(hm.health_check_counter, mock_counter)
        self.assertEqual(hm.prom_health_check_counter, mock_prom)
        mock_meter.create_counter.assert_called_once()
        mock_prom_counter.assert_called_once_with(
            "agent_registry_health_checks_total",
            "Total number of health checks",
            ["status"]
        )

    @patch('marcus.observability.health.Counter')
    def test_setup_without_meter(self, mock_prom_counter):
        mock_prom = MagicMock()
        mock_prom_counter.return_value = mock_prom
        hm = HealthMetrics()
        hm.setup()
        self.assertIsNone(hm.health_check_counter)
        self.assertEqual(hm.prom_health_check_counter, mock_prom)
        mock_prom_counter.assert_called_once()

    def test_record(self):
        hm = HealthMetrics()
        hm.health_check_counter = MagicMock()
        hm.prom_health_check_counter = MagicMock()
        labels_mock = MagicMock()
        hm.prom_health_check_counter.labels.return_value = labels_mock

        hm.record("pass")
        hm.health_check_counter.add.assert_called_once_with(1, {"status": "pass"})
        hm.prom_health_check_counter.labels.assert_called_once_with(status="pass")
        labels_mock.inc.assert_called_once()

    def test_record_no_counters(self):
        hm = HealthMetrics()
        try:
            hm.record("fail")
        except Exception as e:
            self.fail(f"record() raised {type(e).__name__} unexpectedly: {e}")
