import hmac

from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_safe
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


@require_safe
def live(request):
    return JsonResponse({'status': 'ok'})


@require_safe
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        if settings.CACHE_IS_SHARED:
            cache.set('readiness-check', 'ok', timeout=10)
            if cache.get('readiness-check') != 'ok':
                raise RuntimeError('cache unavailable')
        return JsonResponse({'status': 'ready'})
    except Exception:
        return JsonResponse({'status': 'not_ready'}, status=503)


@require_safe
def metrics(request):
    if not settings.METRICS_ENABLED:
        return HttpResponse(status=404)
    expected = settings.METRICS_BEARER_TOKEN
    supplied = request.headers.get('Authorization', '')
    valid = expected and hmac.compare_digest(supplied, f'Bearer {expected}')
    if not settings.DEBUG and not valid:
        return JsonResponse({'error': 'Unauthorized.'}, status=401)
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
