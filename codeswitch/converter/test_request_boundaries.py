from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch


@override_settings(AXES_ENABLED=False)
class RequestBoundaryTests(TestCase):
    def test_valid_admin_module_and_lesson_writes_preserve_defaults_and_content(self):
        from learning.models import Lesson
        get_user_model().objects.update(is_staff=True)
        created = self.client.post('/api/admin/modules', {'title': 'New module'}, format='json')
        self.assertEqual(created.status_code, 201)
        module_id = created.data['id']
        created = self.client.post(f'/api/admin/modules/{module_id}/lessons', {'title': 'First lesson'}, format='json')
        self.assertEqual(created.status_code, 201)
        lesson = Lesson.objects.get(pk=created.data['id'])
        self.assertEqual(lesson.order, 1)
        self.assertEqual(lesson.example_code, '{}')
        content = '  indented Markdown\n'
        updated = self.client.put(f'/api/admin/lessons/{lesson.pk}', {
            'content': content, 'example_code': '{"python":"print(1)"}',
        }, format='json')
        self.assertEqual(updated.status_code, 200)
        lesson.refresh_from_db()
        self.assertEqual(lesson.content, content)
        self.assertEqual(lesson.example_code, '{"python":"print(1)"}')

    def test_file_lists_are_paginated_metadata_and_details_remain_private(self):
        from files.models import CodeFile
        user = get_user_model().objects.get(username='boundary')
        CodeFile.objects.bulk_create([
            CodeFile(user=user, filename=f'{i}.py', language='python', code_content='private source')
            for i in range(51)
        ])
        response = self.client.get('/api/files')
        self.assertEqual(response.data['count'], 51)
        self.assertEqual(len(response.data['results']), 50)
        self.assertNotIn('code_content', response.data['results'][0])
        detail = self.client.get(f"/api/files/{response.data['results'][0]['id']}")
        self.assertEqual(detail.data['code_content'], 'private source')
        other = get_user_model().objects.create_user(username='other-file-user')
        foreign = CodeFile.objects.create(user=other, filename='secret.py', code_content='secret')
        self.assertEqual(self.client.get(f'/api/files/{foreign.pk}').status_code, 404)

    def test_quiz_and_admin_inputs_are_validated_before_use(self):
        from learning.tests import create_module_with_lesson
        module, lesson, quiz, *_ = create_module_with_lesson()
        get_user_model().objects.update(is_staff=True)
        requests = [
            ('post', f'/api/quizzes/{quiz.pk}/submit/', []),
            ('post', '/api/admin/modules', {'title': None}),
            ('post', '/api/admin/modules', {'title': 123}),
            ('put', f'/api/admin/modules/{module.pk}', {'title': 'x' * 201}),
            ('put', f'/api/admin/modules/{module.pk}', {'language': 'invalid'}),
            ('post', f'/api/admin/modules/{module.pk}/lessons', {'title': 'Test', 'order': -1}),
            ('put', f'/api/admin/lessons/{lesson.pk}', {'example_code': '{"python":3}'}),
        ]
        for method, path, data in requests:
            with self.subTest(path=path, data=data):
                cache.clear()
                response = getattr(self.client, method)(path, data, format='json')
                self.assertEqual(response.status_code, 400)
        module.refresh_from_db()
        lesson.refresh_from_db()
        self.assertEqual(module.title, 'Python Basics')
        self.assertEqual(lesson.example_code, 'x = 1')

    @override_settings(DATA_UPLOAD_MAX_MEMORY_SIZE=1024)
    def test_oversized_json_is_rejected_before_field_validation(self):
        response = self.client.post('/api/login', {'username': 'x' * 100_000, 'password': 'x'}, format='json')
        self.assertIn(response.status_code, (400, 413))
        self.assertNotIn('username', getattr(response, 'data', {}))

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
