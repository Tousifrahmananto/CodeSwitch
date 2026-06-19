import logging
import re
import time
import uuid

from django.urls import resolve, Resolver404

from .observability import HTTP_IN_FLIGHT, record_http

logger = logging.getLogger('codeswitch.requests')
REQUEST_ID_RE = re.compile(r'^[A-Za-z0-9._-]{1,128}$')


def _trace_context():
    try:
        from opentelemetry import trace
        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            return f'{context.trace_id:032x}', f'{context.span_id:016x}'
    except Exception:
        pass
    return None, None


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
            response = self.get_response(request)
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
