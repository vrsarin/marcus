import unittest
from unittest.mock import patch, MagicMock
from marcus.observability import tracing as obs_tracing

class TestSetupTracing(unittest.TestCase):
    @patch('marcus.observability.tracing.FastAPIInstrumentor')
    @patch('marcus.observability.tracing.BatchSpanProcessor')
    @patch('marcus.observability.tracing.OTLPSpanExporter')
    @patch('marcus.observability.tracing.TracerProvider')
    @patch('marcus.observability.tracing.trace')
    def test_setup_tracing_defaults(self, mock_trace, mock_tracer_provider, mock_otlp_exporter, mock_batch_span_processor, mock_fastapi_instrumentor):
        app = MagicMock()
        provider = MagicMock()
        mock_tracer_provider.return_value = provider
        otlp_exporter = MagicMock()
        mock_otlp_exporter.return_value = otlp_exporter
        span_processor = MagicMock()
        mock_batch_span_processor.return_value = span_processor

        # Patch Constants
        with patch('marcus.observability.tracing.Constants') as mock_constants:
            mock_constants.MARCUS_OTEL_HOST = 'localhost'
            mock_constants.MARCUS_OTEL_PORT = 4318
            mock_constants.MARCUS_OTEL_PROTOCOL = 'http'
            mock_constants.MARCUS_OTEL_PATH = '/v1/traces'
            mock_constants.MARCUS_OTEL_TIMEOUT = 10

            obs_tracing.setup_tracing(app)

            mock_tracer_provider.assert_called_once()
            mock_trace.set_tracer_provider.assert_called_once_with(provider)
            mock_otlp_exporter.assert_called_once_with(
                endpoint='http://localhost:4318/v1/traces',
                headers={},
                timeout=10
            )
            mock_batch_span_processor.assert_called_once_with(otlp_exporter)
            provider.add_span_processor.assert_called_once_with(span_processor)
            mock_fastapi_instrumentor.instrument_app.assert_called_once_with(app)

    @patch('marcus.observability.tracing.FastAPIInstrumentor')
    @patch('marcus.observability.tracing.BatchSpanProcessor')
    @patch('marcus.observability.tracing.OTLPSpanExporter')
    @patch('marcus.observability.tracing.TracerProvider')
    @patch('marcus.observability.tracing.trace')
    def test_setup_tracing_custom_args(self, mock_trace, mock_tracer_provider, mock_otlp_exporter, mock_batch_span_processor, mock_fastapi_instrumentor):
        app = MagicMock()
        provider = MagicMock()
        mock_tracer_provider.return_value = provider
        otlp_exporter = MagicMock()
        mock_otlp_exporter.return_value = otlp_exporter
        span_processor = MagicMock()
        mock_batch_span_processor.return_value = span_processor

        obs_tracing.setup_tracing(
            app,
            collector_host='customhost',
            collector_port=9999,
            protocol='https',
            endpoint_path='/custom',
            headers={'Authorization': 'Bearer token'},
            timeout=99
        )

        mock_tracer_provider.assert_called_once()
        mock_trace.set_tracer_provider.assert_called_once_with(provider)
        mock_otlp_exporter.assert_called_once_with(
            endpoint='https://customhost:9999/custom',
            headers={'Authorization': 'Bearer token'},
            timeout=99
        )
        mock_batch_span_processor.assert_called_once_with(otlp_exporter)
        provider.add_span_processor.assert_called_once_with(span_processor)
        mock_fastapi_instrumentor.instrument_app.assert_called_once_with(app)