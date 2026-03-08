from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

VALID_USER = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'Test1234!',
}

# Registration requires password confirmation
REGISTER_DATA = {**VALID_USER, 'password2': 'Test1234!'}


@override_settings(AXES_ENABLED=False)
class RegistrationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_register_valid(self):
        response = self.client.post('/api/register', REGISTER_DATA, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_duplicate_username(self):
        User.objects.create_user(**VALID_USER)
        response = self.client.post('/api/register', REGISTER_DATA, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_missing_field(self):
        response = self.client.post('/api/register', {'username': 'u', 'password': 'Test1234!'}, format='json')
        self.assertEqual(response.status_code, 400)


@override_settings(AXES_ENABLED=False)
class LoginTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(**VALID_USER)

    def test_login_with_username_sets_cookies(self):
        response = self.client.post('/api/login',
            {'username': 'testuser', 'password': 'Test1234!'},
            format='json')
        self.assertEqual(response.status_code, 200)
        # Tokens must be in httpOnly cookies, not response body
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])
        # Response body should contain only the user object
        self.assertIn('user', response.data)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_login_with_email(self):
        response = self.client.post('/api/login',
            {'username': 'test@example.com', 'password': 'Test1234!'},
            format='json')
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_password(self):
        response = self.client.post('/api/login',
            {'username': 'testuser', 'password': 'wrongpassword'},
            format='json')
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        response = self.client.post('/api/login',
            {'username': 'nobody', 'password': 'Test1234!'},
            format='json')
        self.assertEqual(response.status_code, 401)


@override_settings(AXES_ENABLED=False)
class LogoutTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(**VALID_USER)
        # Log in to get cookies
        self.client.post('/api/login',
            {'username': 'testuser', 'password': 'Test1234!'},
            format='json')

    def test_logout_clears_cookies(self):
        response = self.client.post('/api/logout', format='json')
        self.assertEqual(response.status_code, 200)
        # Cookies should be deleted (max-age=0 or empty value)
        if 'access_token' in response.cookies:
            self.assertEqual(response.cookies['access_token'].value, '')
        if 'refresh_token' in response.cookies:
            self.assertEqual(response.cookies['refresh_token'].value, '')


@override_settings(AXES_ENABLED=False)
class MeViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(**VALID_USER)

    def _set_auth_cookie(self):
        """Helper: set a valid access_token cookie on the test client."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['access_token'] = str(refresh.access_token)

    def test_me_authenticated(self):
        self._set_auth_cookie()
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')

    def test_me_unauthenticated(self):
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, 401)


@override_settings(AXES_ENABLED=False)
class ProfileTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(**VALID_USER)
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['access_token'] = str(refresh.access_token)

    def test_profile_get(self):
        response = self.client.get('/api/profile')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')

    def test_profile_update(self):
        response = self.client.patch('/api/profile',
            {'first_name': 'Updated', 'bio': 'New bio'},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.bio, 'New bio')
