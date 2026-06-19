from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def authed_client(user):
    client = APIClient()
    client.cookies['access_token'] = str(RefreshToken.for_user(user).access_token)
    return client


@override_settings(AXES_ENABLED=False)
class EndpointThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('rate_user', 'rate@example.com', 'Test1234!')

    def tearDown(self):
        cache.clear()

    @patch('converter.views._pick_compiler', return_value='cpython-3.12')
    @patch('converter.views.http_requests.post')
    def test_authenticated_run_is_rate_limited(self, request_post, _compiler):
        request_post.return_value.raise_for_status.return_value = None
        request_post.return_value.json.return_value = {'status': '0'}
        client = authed_client(self.user)
        payload = {'language': 'python', 'code': 'print(1)'}
        for _ in range(30):
            self.assertEqual(client.post('/api/run/', payload, format='json').status_code, 200)
        response = client.post('/api/run/', payload, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data['scope'], 'run_user')
        self.assertIn('Retry-After', response)

    def test_snippet_ip_limit_applies_to_authenticated_user(self):
        client = authed_client(self.user)
        url = '/api/snippets/00000000-0000-0000-0000-000000000000/'
        for _ in range(60):
            self.assertEqual(client.get(url).status_code, 404)
        response = client.get(url)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data['scope'], 'snippet_ip')

    def test_registration_has_dedicated_limit(self):
        client = APIClient()
        for index in range(5):
            payload = {
                'username': f'user{index}', 'email': f'user{index}@example.com',
                'password': 'Test1234!', 'password2': 'Test1234!',
            }
            self.assertEqual(
                client.post(
                    '/api/register', payload, format='json',
                    HTTP_X_FORWARDED_FOR=f'203.0.113.{index + 1}',
                ).status_code,
                201,
            )
        payload.update(username='blocked', email='blocked@example.com')
        response = client.post(
            '/api/register', payload, format='json', HTTP_X_FORWARDED_FOR='198.51.100.99'
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data['scope'], 'register')
