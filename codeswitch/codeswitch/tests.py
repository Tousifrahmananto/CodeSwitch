from django.db import OperationalError
from django.test import TestCase, override_settings



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

    def test_real_api_stack_maps_transient_database_errors_without_replaying_writes(self):
        from django.contrib.auth import get_user_model
        from django.core.cache import cache
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        from unittest.mock import patch
        cache.clear()
        self.addCleanup(cache.clear)
        user = get_user_model().objects.create_user(username='database', password='Test1234!')
        client = APIClient(raise_request_exception=False)
        client.cookies['access_token'] = str(RefreshToken.for_user(user).access_token)
        with patch('converter.views.convert_code', return_value={'success': True, 'output': 'output', 'engine': 'rules'}), \
             patch('converter.views.ConversionHistory.objects.create', side_effect=OperationalError('the database system is starting up')) as write:
            response = client.post('/api/convert', {'source_language': 'python', 'target_language': 'c', 'code': 'print(1)'}, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '2')
        self.assertEqual(response.data, {'error': 'Service temporarily unavailable. Please retry shortly.'})
        self.assertEqual(write.call_count, 1)

    def test_unrecognized_database_errors_are_not_disguised_as_transient(self):
        from .exception_handler import api_exception_handler
        self.assertIsNone(api_exception_handler(OperationalError('syntax error in SQL'), {}))
