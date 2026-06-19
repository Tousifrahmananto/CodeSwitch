import logging

from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler as drf_exception_handler

from .observability import record_throttled

logger = logging.getLogger('codeswitch.throttling')


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
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
