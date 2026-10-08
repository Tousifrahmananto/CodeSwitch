import logging

from django.db import OperationalError
from rest_framework.response import Response

from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler

from .observability import record_throttled

logger = logging.getLogger('codeswitch.throttling')


TRANSIENT_DATABASE_ERROR_MARKERS = (
    'database system is starting up',
    'database system is not yet accepting connections',
    'consistent recovery state has not been yet reached',
    'could not connect to server',
    'connection refused',
    'server closed the connection unexpectedly',
)


def api_exception_handler(exc, context):
    if isinstance(exc, OperationalError) and any(marker in str(exc).lower() for marker in TRANSIENT_DATABASE_ERROR_MARKERS):
        request = context.get('request')
        logger.warning('database_temporarily_unavailable', extra={'request_id': getattr(request, 'request_id', None)})
        return Response({'error': 'Service temporarily unavailable. Please retry shortly.'},
                        status=503, headers={'Retry-After': '2'})
    response = drf_exception_handler(exc, context)
    if isinstance(exc, ValidationError) and response is not None and isinstance(response.data, dict) and 'error' not in response.data:
        response.data['error'] = ' '.join(str(message) for messages in response.data.values()
                                          for message in (messages if isinstance(messages, list) else [messages]))
    if isinstance(exc, Throttled) and response is not None:
        request = context.get('request')
        scope = getattr(request, '_throttle_scope', 'global')
        retry_after = max(1, int(exc.wait or 1))
        response.data = {'error': 'Rate limit exceeded.', 'scope': scope, 'retry_after': retry_after}
        response['Retry-After'] = str(retry_after)
        record_throttled(scope)
        logger.warning('rate_limit_rejected', extra={
            'request_id': getattr(request, 'request_id', None), 'scope': scope,
            'method': getattr(request, 'method', None),
        })
    return response
