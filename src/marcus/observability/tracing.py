from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from marcus.settings import Constants


def setup_tracing(
    app,
    collector_host: Optional[str] = None,
    collector_port: Optional[int] = None,
    protocol: Optional[str] = None,
    endpoint_path: Optional[str] = None,
    headers: Optional[dict] = None,
    timeout: Optional[int] = None,
):
    """
    Set up OpenTelemetry tracing for FastAPI app with custom collector endpoint and credentials.
    """


    collector_host = collector_host or Constants.MARCUS_OTEL_HOST
    collector_port = collector_port or Constants.MARCUS_OTEL_PORT
    protocol = protocol or Constants.MARCUS_OTEL_PROTOCOL
    endpoint_path = endpoint_path or Constants.MARCUS_OTEL_PATH
    headers = headers or {}
    timeout = timeout or Constants.MARCUS_OTEL_TIMEOUT


    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    endpoint = f"{protocol}://{collector_host}:{collector_port}{endpoint_path}"
    otlp_exporter = OTLPSpanExporter(
        endpoint=endpoint,
        headers=headers,
        timeout=timeout,
    )
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    FastAPIInstrumentor.instrument_app(app)
