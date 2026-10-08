from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch


@override_settings(AXES_ENABLED=False)
class RequestBoundaryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        user = get_user_model().objects.create_user(username='boundary', password='Test1234!')
        self.client = APIClient(raise_request_exception=False)
        self.client.cookies['access_token'] = str(RefreshToken.for_user(user).access_token)

    def test_invalid_fields_are_controlled_errors(self):
        requests = [
            ('/api/convert', {'source_language': 'python', 'target_language': 'c', 'code': 'print(1)'}),
            ('/api/run/', {'language': 'python', 'code': 'print(1)', 'stdin': ''}),
            ('/api/verify', {'source_language': 'python', 'target_language': 'c', 'source_code': 'print(1)', 'target_code': 'puts("1");', 'stdin': ''}),
            ('/api/explain/', {'source_language': 'python', 'target_language': 'c', 'input_code': 'print(1)', 'output_code': 'puts("1");'}),
            ('/api/visualize', {'language': 'python', 'code': 'print(1)'}),
        ]
        for path, payload in requests:
            for field in payload:
                for invalid in (None, 3, True, [], {}):
                    with self.subTest(path=path, field=field, invalid=invalid):
                        cache.clear()
                        response = self.client.post(path, {**payload, field: invalid}, format='json')
                        self.assertEqual(response.status_code, 400)
            cache.clear()
            self.assertEqual(self.client.post(path, ['invalid root'], format='json').status_code, 400)

    def test_progress_ids_are_validated(self):
        for invalid in (None, [], {}, 'bad', 0, -1, 1.5, True, 2**63):
            with self.subTest(invalid=invalid):
                cache.clear()
                response = self.client.post('/api/progress/update', {'lesson_id': invalid}, format='json')
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post('/api/progress/update', {'lesson_id': 999_999}, format='json').status_code, 404)

    def test_all_code_and_stdin_length_limits_are_preserved(self):
        requests = [
            ('/api/convert', {'source_language': 'python', 'target_language': 'c', 'code': 'x'}, ['code'], 50_000),
            ('/api/explain/', {'source_language': 'python', 'target_language': 'c', 'input_code': 'x', 'output_code': 'x'}, ['input_code', 'output_code'], 50_000),
            ('/api/run/', {'language': 'python', 'code': 'x', 'stdin': ''}, ['code', 'stdin'], 10_000),
            ('/api/verify', {'source_language': 'python', 'target_language': 'c', 'source_code': 'x', 'target_code': 'x', 'stdin': ''}, ['source_code', 'target_code', 'stdin'], 10_000),
            ('/api/visualize', {'language': 'python', 'code': 'x'}, ['code'], 20_000),
        ]
        for path, payload, fields, limit in requests:
            for field in fields:
                with self.subTest(path=path, field=field):
                    cache.clear()
                    response = self.client.post(path, {**payload, field: 'x' * (limit + 1)}, format='json')
                    self.assertEqual(response.status_code, 400)

    def test_empty_files_can_be_created_and_saved(self):
        created = self.client.post('/api/files', {'filename': 'empty.py', 'language': 'python', 'code_content': ''}, format='json')
        self.assertEqual(created.status_code, 201)
        saved = self.client.patch(f"/api/files/{created.data['id']}", {'code_content': ''}, format='json')
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.data['code_content'], '')

    @patch('converter.views.convert_code', return_value={'success': True, 'output': 'output', 'engine': 'rules'})
    def test_language_normalization_preserves_code_whitespace(self, convert):
        response = self.client.post('/api/convert', {'source_language': ' Python ', 'target_language': ' C ', 'code': '  print(1)\n'}, format='json')
        self.assertEqual(response.status_code, 200)
        convert.assert_called_once_with('python', 'c', '  print(1)\n', user_key=None)
