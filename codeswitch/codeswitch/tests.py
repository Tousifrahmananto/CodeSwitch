import json

from django.db import OperationalError
from django.http import JsonResponse
from django.test import RequestFactory
from django.test import TestCase, override_settings

from .middleware import RequestObservabilityMiddleware


class HealthAndRequestIdTests(TestCase):
    def test_live_endpoint_and_request_id(self):
        response = self.client.get('/health/live', HTTP_X_REQUEST_ID='test-request-123')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Request-ID'], 'test-request-123')
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_invalid_request_id_is_replaced(self):
        response = self.client.get('/health/live', HTTP_X_REQUEST_ID='invalid request id')
        self.assertNotEqual(response['X-Request-ID'], 'invalid request id')

    def test_ready_endpoint(self):
        response = self.client.get('/health/ready')
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=False, METRICS_ENABLED=True, METRICS_BEARER_TOKEN='metrics-secret')
    def test_metrics_requires_bearer_token_in_production(self):
        denied = self.client.get('/metrics')
        self.assertEqual(denied.status_code, 401)
        allowed = self.client.get('/metrics', HTTP_AUTHORIZATION='Bearer metrics-secret')
        self.assertEqual(allowed.status_code, 200)
        self.assertIn('codeswitch_http_requests_total', allowed.content.decode())

    @override_settings(METRICS_ENABLED=False)
    def test_disabled_metrics_are_hidden(self):
        self.assertEqual(self.client.get('/metrics').status_code, 404)

    @override_settings(DB_REQUEST_RETRY_ATTEMPTS=2, DB_REQUEST_RETRY_DELAY_SECONDS=0)
    def test_transient_database_startup_error_is_retried(self):
        calls = {'count': 0}

        def get_response(request):
            calls['count'] += 1
            if calls['count'] == 1:
                raise OperationalError('the database system is starting up')
            return JsonResponse({'status': 'ok'})

        middleware = RequestObservabilityMiddleware(get_response)
        response = middleware(RequestFactory().get('/api/me/'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls['count'], 2)

    @override_settings(DB_REQUEST_RETRY_ATTEMPTS=1, DB_REQUEST_RETRY_DELAY_SECONDS=0)
    def test_transient_database_startup_error_returns_503_after_retries(self):
        def get_response(request):
            raise OperationalError('the database system is not yet accepting connections')

        middleware = RequestObservabilityMiddleware(get_response)
        response = middleware(RequestFactory().get('/api/me/'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '2')
        self.assertEqual(
            json.loads(response.content.decode()),
            {'error': 'Service temporarily unavailable. Please retry shortly.'},
        )
