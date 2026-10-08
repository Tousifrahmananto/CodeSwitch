from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
from io import BytesIO
from unittest.mock import patch
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

VALID_USER = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'Test1234!',
}

# Registration requires password confirmation
REGISTER_DATA = {**VALID_USER, 'password2': 'Test1234!'}


@override_settings(AXES_ENABLED=False)
class SessionRecoveryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.user = User.objects.create_user(**VALID_USER)
        self.refresh = RefreshToken.for_user(self.user)
        self.client = APIClient()
        self.client.cookies['refresh_token'] = str(self.refresh)

    def test_refresh_rotates_and_blacklists_previous_token(self):
        response = self.client.post('/api/token/refresh/')
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.cookies['refresh_token'].value, str(self.refresh))
        with self.assertRaises(TokenError):
            RefreshToken(str(self.refresh))
        for name, token_class in [('access_token', AccessToken), ('refresh_token', RefreshToken)]:
            token = token_class(response.cookies[name].value)
            remaining = token['exp'] - int(token.current_time.timestamp())
            self.assertAlmostEqual(int(response.cookies[name]['max-age']), remaining, delta=1)

    def test_disabled_or_deleted_refresh_users_are_rejected_and_cookies_cleared(self):
        for deleted in (False, True):
            with self.subTest(deleted=deleted):
                if deleted:
                    self.user.delete()
                else:
                    self.user.is_active = False
                    self.user.save(update_fields=['is_active'])
                self.client.cookies['refresh_token'] = str(self.refresh)
                response = self.client.post('/api/token/refresh/')
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.cookies['access_token']['max-age'], 0)
                self.assertEqual(response.cookies['refresh_token']['max-age'], 0)

    def test_disabled_or_deleted_access_user_can_logout_and_login_with_csrf(self):
        other = User.objects.create_user(username='other', password='Test1234!')
        for deleted in (False, True):
            with self.subTest(deleted=deleted):
                if deleted:
                    self.user.delete()
                else:
                    self.user.is_active = False
                    self.user.save(update_fields=['is_active'])
                client = APIClient(enforce_csrf_checks=True)
                client.cookies['access_token'] = str(self.refresh.access_token)
                self.assertEqual(client.post('/api/logout').status_code, 403)
                csrf = client.get('/api/csrf/').data['csrf_token']
                self.assertEqual(client.post('/api/logout', HTTP_X_CSRFTOKEN=csrf).status_code, 200)
                client.cookies['access_token'] = str(self.refresh.access_token)
                response = client.post('/api/login', {'username': other.username, 'password': 'Test1234!'},
                                       format='json', HTTP_X_CSRFTOKEN=csrf)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['user']['id'], other.pk)

    def test_refresh_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.cookies['refresh_token'] = str(self.refresh)
        self.assertEqual(client.post('/api/token/refresh/').status_code, 403)

    def test_cookie_lifetimes_follow_actual_token_expiry(self):
        from datetime import timedelta
        from rest_framework.response import Response
        from users.views import _set_auth_cookies
        self.refresh.set_exp(lifetime=timedelta(minutes=4))
        access = self.refresh.access_token
        access.set_exp(lifetime=timedelta(seconds=30))
        response = Response()
        _set_auth_cookies(response, self.refresh, str(access))
        self.assertAlmostEqual(response.cookies['access_token']['max-age'], 30, delta=1)
        self.assertAlmostEqual(response.cookies['refresh_token']['max-age'], 240, delta=1)


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
        cache.clear()
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

    def test_login_requires_csrf_in_real_client_mode(self):
        client = APIClient(enforce_csrf_checks=True)
        payload = {'username': 'testuser', 'password': 'Test1234!'}
        self.assertEqual(client.post('/api/login', payload, format='json').status_code, 403)

        csrf_response = client.get('/api/csrf/')
        token = csrf_response.data['csrf_token']
        response = client.post('/api/login', payload, format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)


@override_settings(AXES_ENABLED=False, GOOGLE_OAUTH_CLIENT_ID='google-client-id.apps.googleusercontent.com')
class GoogleAuthTests(TestCase):

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def _payload(self, **overrides):
        payload = {
            'sub': 'google-sub-123',
            'email': 'google@example.com',
            'email_verified': True,
            'given_name': 'Googly',
            'family_name': 'User',
        }
        payload.update(overrides)
        return payload

    @patch('users.views.id_token.verify_oauth2_token')
    def test_overlapping_first_google_signins_resolve_only_matching_identity(self, verify):
        from django.db.models.query import QuerySet
        verify.return_value = self._payload()
        winner = User.objects.create_user(username='winning', email='google@example.com',
                                          google_sub='google-sub-123', email_verified=True)
        original_first = QuerySet.first
        for unrelated in (False, True):
            with self.subTest(unrelated=unrelated):
                winner.google_sub = 'another-google-sub' if unrelated else 'google-sub-123'
                winner.save(update_fields=['google_sub'])
                reads = [0]
                def stale_first(queryset):
                    if queryset.model is User and reads[0] < 2:
                        reads[0] += 1
                        return None
                    return original_first(queryset)
                client = APIClient(raise_request_exception=False)
                with patch.object(QuerySet, 'first', stale_first):
                    response = client.post('/api/auth/google', {'credential': 'id-token'}, format='json')
                self.assertEqual(response.status_code, 409 if unrelated else 200)
                self.assertEqual(User.objects.count(), 1)
                if not unrelated:
                    self.assertEqual(response.data['user']['id'], winner.pk)
                else:
                    self.assertNotIn('access_token', response.cookies)

    @patch('users.views.id_token.verify_oauth2_token')
    def test_google_auth_creates_user_and_sets_cookies(self, verify_mock):
        verify_mock.return_value = self._payload()
        response = self.client.post('/api/auth/google', {'credential': 'id-token'}, format='json')

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='google@example.com')
        self.assertEqual(user.google_sub, 'google-sub-123')
        self.assertTrue(user.google_email_verified)
        self.assertTrue(user.email_verified)
        self.assertFalse(user.has_usable_password())
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertEqual(response.data['user']['email'], 'google@example.com')

    @patch('users.views.id_token.verify_oauth2_token')
    def test_google_auth_does_not_import_google_profile_picture(self, verify_mock):
        verify_mock.return_value = self._payload(
            picture='https://lh3.googleusercontent.com/a/google-avatar'
        )

        response = self.client.post('/api/auth/google', {'credential': 'id-token'}, format='json')

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='google@example.com')
        self.assertFalse(user.avatar)
        self.assertIsNone(response.data['user']['avatar'])

    @patch('users.views.id_token.verify_oauth2_token')
    def test_google_auth_links_existing_verified_email(self, verify_mock):
        existing = User.objects.create_user(
            username='existing',
            email='google@example.com',
            password='Test1234!',
            email_verified=True,
        )
        verify_mock.return_value = self._payload(given_name='Linked')

        response = self.client.post('/api/auth/google', {'credential': 'id-token'}, format='json')

        self.assertEqual(response.status_code, 200)
        existing.refresh_from_db()
        self.assertEqual(existing.google_sub, 'google-sub-123')
        self.assertEqual(existing.first_name, 'Linked')
        self.assertEqual(User.objects.count(), 1)

    @patch('users.views.id_token.verify_oauth2_token')
    def test_google_auth_does_not_link_unverified_local_email(self, verify_mock):
        existing = User.objects.create_user(
            username='unverified',
            email='google@example.com',
            password='Test1234!',
        )
        verify_mock.return_value = self._payload()

        response = self.client.post('/api/auth/google', {'credential': 'id-token'}, format='json')

        self.assertEqual(response.status_code, 409)
        existing.refresh_from_db()
        self.assertIsNone(existing.google_sub)

    @patch('users.views.id_token.verify_oauth2_token')
    def test_google_auth_existing_google_sub_signs_in_same_user(self, verify_mock):
        user = User.objects.create_user(
            username='googleuser',
            email='old@example.com',
            password='Test1234!',
            google_sub='google-sub-123',
            google_email_verified=True,
        )
        verify_mock.return_value = self._payload(email='new@example.com')

        response = self.client.post('/api/auth/google', {'credential': 'id-token'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['id'], user.id)
        self.assertEqual(User.objects.count(), 1)

    @patch('users.views.id_token.verify_oauth2_token')
    def test_google_auth_rejects_invalid_token(self, verify_mock):
        verify_mock.side_effect = ValueError('bad token')
        response = self.client.post('/api/auth/google', {'credential': 'bad-token'}, format='json')
        self.assertEqual(response.status_code, 401)

    @patch('users.views.id_token.verify_oauth2_token')
    def test_google_auth_rejects_unverified_email(self, verify_mock):
        verify_mock.return_value = self._payload(email_verified=False)
        response = self.client.post('/api/auth/google', {'credential': 'id-token'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_google_auth_requires_config(self):
        with override_settings(GOOGLE_OAUTH_CLIENT_ID=''):
            response = self.client.post('/api/auth/google', {'credential': 'id-token'}, format='json')
        self.assertEqual(response.status_code, 503)


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

    def test_me_includes_absolute_avatar_url(self):
        self.user.avatar.name = 'avatars/test.png'
        self.user.save(update_fields=['avatar'])
        self._set_auth_cookie()
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['avatar'],
            'http://testserver/media/avatars/test.png',
        )

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

    def test_staff_flag_is_private_and_cannot_be_granted_by_profile_writes(self):
        self.assertFalse(self.client.get('/api/profile').data['is_staff'])
        response = self.client.patch('/api/profile', {'is_staff': True}, format='json')
        self.assertFalse(response.data['is_staff'])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.user.is_staff = True
        self.user.save(update_fields=['is_staff'])
        self.assertTrue(self.client.get('/api/me/').data['is_staff'])
        self.assertNotIn('is_staff', self.client.get('/api/profile/testuser/').data)

    def test_profile_get_includes_absolute_avatar_url(self):
        self.user.avatar.name = 'avatars/test.png'
        self.user.save(update_fields=['avatar'])
        response = self.client.get('/api/profile')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['avatar'],
            'http://testserver/media/avatars/test.png',
        )

    def test_profile_update(self):
        response = self.client.patch('/api/profile',
            {'first_name': 'Updated', 'bio': 'New bio'},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.bio, 'New bio')

    def test_avatar_rejects_oversized_and_disallowed_images_before_storage(self):
        for image_format, content_type, padding in [
            ('PNG', 'image/png', b'x' * (5 * 1024 * 1024)),
            ('GIF', 'image/gif', b''),
        ]:
            with self.subTest(content_type=content_type):
                image = BytesIO()
                Image.new('RGB', (1, 1)).save(image, format=image_format)
                avatar = SimpleUploadedFile('avatar.' + image_format.lower(),
                                            image.getvalue() + padding, content_type=content_type)
                response = self.client.patch('/api/profile', {'avatar': avatar}, format='multipart')
                self.assertEqual(response.status_code, 400)
                self.user.refresh_from_db()
                self.assertFalse(self.user.avatar_blob)
                self.assertFalse(self.user.avatar)

    def test_cookie_authenticated_profile_write_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        client.cookies['access_token'] = str(RefreshToken.for_user(self.user).access_token)

        rejected = client.patch('/api/profile', {'first_name': 'Blocked'}, format='json')
        self.assertEqual(rejected.status_code, 403)

        csrf_response = client.get('/api/csrf/')
        accepted = client.patch(
            '/api/profile',
            {'first_name': 'Allowed'},
            format='json',
            HTTP_X_CSRFTOKEN=csrf_response.data['csrf_token'],
        )
        self.assertEqual(accepted.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Allowed')

    def test_profile_avatar_upload_persists_after_reload(self):
        image = BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(image, format='PNG')
        image.seek(0)
        avatar = SimpleUploadedFile(
            'avatar.png',
            image.read(),
            content_type='image/png',
        )

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.patch('/api/profile', {'avatar': avatar}, format='multipart')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data['avatar'].startswith('data:image/png;base64,'))

            self.user.refresh_from_db()
            self.assertFalse(self.user.avatar)
            self.assertTrue(self.user.avatar_blob)
            self.assertEqual(self.user.avatar_content_type, 'image/png')
            self.assertEqual(self.user.avatar_filename, 'avatar.png')

            reload_response = self.client.get('/api/profile')
            self.assertEqual(reload_response.status_code, 200)
            self.assertEqual(reload_response.data['avatar'], response.data['avatar'])

    def test_public_profile_includes_db_backed_avatar(self):
        self.user.avatar_blob = b'avatar-bytes'
        self.user.avatar_content_type = 'image/png'
        self.user.avatar_filename = 'avatar.png'
        self.user.save(update_fields=['avatar_blob', 'avatar_content_type', 'avatar_filename'])

        response = self.client.get('/api/profile/testuser/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['avatar'],
            'data:image/png;base64,YXZhdGFyLWJ5dGVz',
        )

    def test_public_profile_includes_absolute_avatar_url(self):
        self.user.avatar.name = 'avatars/test.png'
        self.user.save(update_fields=['avatar'])
        response = self.client.get('/api/profile/testuser/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['avatar'],
            'http://testserver/media/avatars/test.png',
        )
