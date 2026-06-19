"""Metrics and OpenTelemetry setup with safe no-export defaults."""
import logging
import os
import time

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

HTTP_REQUESTS = Counter(
    'codeswitch_http_requests_total', 'HTTP requests', ['method', 'route', 'status']
)
HTTP_DURATION = Histogram(
    'codeswitch_http_request_duration_seconds', 'HTTP request duration',
    ['method', 'route'], buckets=(.01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10)
)
HTTP_IN_FLIGHT = Gauge(
    'codeswitch_http_requests_in_flight', 'HTTP requests currently being served', ['method']
)
THROTTLED = Counter(
    'codeswitch_rate_limit_rejections_total', 'Rate-limit rejections', ['scope']
)
CONVERSIONS = Counter(
    'codeswitch_conversions_total', 'Code conversion attempts', ['engine', 'status']
)
DEPENDENCY_CALLS = Counter(
    'codeswitch_dependency_calls_total', 'External dependency calls', ['dependency', 'status']
)
DEPENDENCY_DURATION = Histogram(
    'codeswitch_dependency_duration_seconds', 'External dependency latency', ['dependency']
)

_otel_meter = None
_otel_http_counter = None
_otel_http_duration = None
_otel_conversion_counter = None
_otel_dependency_counter = None
_otel_dependency_duration = None
_otel_throttled_counter = None


def configure_opentelemetry():
    """Configure OTLP tracing and metrics only when an endpoint is supplied."""
    global _otel_meter, _otel_http_counter, _otel_http_duration
    global _otel_conversion_counter, _otel_dependency_counter, _otel_dependency_duration, _otel_throttled_counter
    endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', '').strip()
    if not endpoint:
        return
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

        resource = Resource.create({
            'service.name': os.getenv('SERVICE_NAME', 'codeswitch-backend'),
            'deployment.environment': os.getenv('DEPLOYMENT_ENVIRONMENT', 'development'),
        })
        trace_provider = TracerProvider(resource=resource)
        trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(trace_provider)

        interval = int(os.getenv('OTEL_METRICS_EXPORT_INTERVAL', '60000'))
        reader = PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=interval)
        meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(meter_provider)
        _otel_meter = metrics.get_meter('codeswitch')
        _otel_http_counter = _otel_meter.create_counter('codeswitch.http.requests')
        _otel_http_duration = _otel_meter.create_histogram('codeswitch.http.duration', unit='s')
        _otel_conversion_counter = _otel_meter.create_counter('codeswitch.conversions')
        _otel_dependency_counter = _otel_meter.create_counter('codeswitch.dependency.calls')
        _otel_dependency_duration = _otel_meter.create_histogram('codeswitch.dependency.duration', unit='s')
        _otel_throttled_counter = _otel_meter.create_counter('codeswitch.rate_limit.rejections')
        RequestsInstrumentor().instrument()
        Psycopg2Instrumentor().instrument(enable_commenter=False)

        # JSON remains on stdout for Railway; this second handler ships the same
        # sanitized records to Grafana Cloud Loki when OTLP logs are accepted.
        try:
            from opentelemetry import _logs
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
            from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
            log_provider = LoggerProvider(resource=resource)
            log_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
            _logs.set_logger_provider(log_provider)
            logging.getLogger().addHandler(LoggingHandler(logger_provider=log_provider))
        except Exception:
            logger.warning('otel_log_export_unavailable')
    except Exception:
        logger.exception('observability_setup_failed')


def record_http(method, route, status, duration):
    attrs = {'http.request.method': method, 'http.route': route, 'http.response.status_code': status}
    HTTP_REQUESTS.labels(method, route, str(status)).inc()
    HTTP_DURATION.labels(method, route).observe(duration)
    if _otel_http_counter:
        _otel_http_counter.add(1, attrs)
        _otel_http_duration.record(duration, attrs)


def record_conversion(engine, status):
    CONVERSIONS.labels(engine, status).inc()
    if _otel_conversion_counter:
        _otel_conversion_counter.add(1, {'codeswitch.engine': engine, 'codeswitch.status': status})


def record_throttled(scope):
    THROTTLED.labels(scope).inc()
    if _otel_throttled_counter:
        _otel_throttled_counter.add(1, {'codeswitch.scope': scope})


class dependency_timer:
    def __init__(self, dependency):
        self.dependency = dependency

    def __enter__(self):
        self.started = time.monotonic()
        return self

    def __exit__(self, exc_type, exc, tb):
        duration = time.monotonic() - self.started
        status = 'error' if exc else 'success'
        DEPENDENCY_DURATION.labels(self.dependency).observe(duration)
        DEPENDENCY_CALLS.labels(self.dependency, status).inc()
        if _otel_dependency_counter:
            attrs = {'codeswitch.dependency': self.dependency, 'codeswitch.status': status}
            _otel_dependency_counter.add(1, attrs)
            _otel_dependency_duration.record(duration, attrs)
        return False
