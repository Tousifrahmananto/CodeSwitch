import logging
import re
import time
import uuid

from django.conf import settings
from django.db import OperationalError, close_old_connections
from django.http import JsonResponse
from django.urls import resolve, Resolver404

from .observability import HTTP_IN_FLIGHT, record_http

logger = logging.getLogger('codeswitch.requests')
REQUEST_ID_RE = re.compile(r'^[A-Za-z0-9._-]{1,128}$')
TRANSIENT_DATABASE_ERROR_MARKERS = (
    'database system is starting up',
    'database system is not yet accepting connections',
    'consistent recovery state has not been yet reached',
    'could not connect to server',
    'connection refused',
    'server closed the connection unexpectedly',
)


def _trace_context():
    try:
        from opentelemetry import trace
        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            return f'{context.trace_id:032x}', f'{context.span_id:016x}'
    except Exception:
        pass
    return None, None


def _is_transient_database_startup_error(exc):
    message = str(exc).lower()
    return any(marker in message for marker in TRANSIENT_DATABASE_ERROR_MARKERS)


class RequestObservabilityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        supplied = request.headers.get('X-Request-ID', '')
        request.request_id = supplied if REQUEST_ID_RE.fullmatch(supplied) else str(uuid.uuid4())
        method = request.method
        HTTP_IN_FLIGHT.labels(method).inc()
        started = time.monotonic()
        response = None
        try:
            attempts = max(1, getattr(settings, 'DB_REQUEST_RETRY_ATTEMPTS', 3))
            base_delay = max(0, getattr(settings, 'DB_REQUEST_RETRY_DELAY_SECONDS', 0.25))
            for attempt in range(attempts):
                try:
                    response = self.get_response(request)
                    break
                except OperationalError as exc:
                    is_transient = _is_transient_database_startup_error(exc)
                    if not is_transient:
                        raise
                    close_old_connections()
                    if attempt >= attempts - 1:
                        logger.warning('database_temporarily_unavailable', extra={
                            'request_id': request.request_id,
                            'method': method,
                            'path': request.path,
                            'attempts': attempts,
                        })
                        response = JsonResponse(
                            {'error': 'Service temporarily unavailable. Please retry shortly.'},
                            status=503,
                        )
                        response['Retry-After'] = '2'
                        break
                    sleep_for = base_delay * (attempt + 1)
                    logger.warning('database_connection_retry', extra={
                        'request_id': request.request_id,
                        'method': method,
                        'path': request.path,
                        'attempt': attempt + 1,
                        'next_delay_seconds': sleep_for,
                    })
                    time.sleep(sleep_for)
            return response
        finally:
            duration = time.monotonic() - started
            HTTP_IN_FLIGHT.labels(method).dec()
            try:
                match = resolve(request.path_info)
                route = match.route or 'unknown'
            except Resolver404:
                route = 'unmatched'
            status = getattr(response, 'status_code', 500)
            record_http(method, route, status, duration)
            trace_id, span_id = _trace_context()
            logger.info('request_completed', extra={
                'request_id': request.request_id, 'trace_id': trace_id, 'span_id': span_id,
                'method': method, 'route': route, 'status': status,
                'duration_ms': round(duration * 1000, 2),
                'user_id': getattr(getattr(request, 'user', None), 'pk', None),
            })
            if response is not None:
                response['X-Request-ID'] = request.request_id
