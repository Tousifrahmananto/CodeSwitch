from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

User = get_user_model()

SAMPLE_PYTHON = "x = 1\nprint(x)\n"
SAMPLE_JAVA = "public class Main {\n    public static void main(String[] args) {\n        int x = 1;\n        System.out.println(x);\n    }\n}\n"


def _make_authed_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.cookies['access_token'] = str(refresh.access_token)
    return client


@override_settings(AXES_ENABLED=False)
class ConvertCodeTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='converter_user', email='conv@example.com', password='Test1234!')
        self.client = _make_authed_client(self.user)

    def test_convert_requires_auth(self):
        anon = APIClient()
        response = anon.post('/api/convert',
            {'source_language': 'python', 'target_language': 'java', 'code': SAMPLE_PYTHON},
            format='json')
        self.assertEqual(response.status_code, 401)

    @patch('converter.views.convert_code')
    def test_convert_valid(self, mock_convert):
        mock_convert.return_value = {'success': True, 'output': SAMPLE_JAVA, 'engine': 'ai'}
        response = self.client.post('/api/convert',
            {'source_language': 'python', 'target_language': 'java', 'code': SAMPLE_PYTHON},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('output', response.data)

    def test_convert_invalid_language(self):
        response = self.client.post('/api/convert',
            {'source_language': 'ruby', 'target_language': 'python', 'code': 'puts "hi"'},
            format='json')
        self.assertEqual(response.status_code, 400)

    def test_convert_code_too_long(self):
        huge_code = 'x = 1\n' * 10_000  # > 50,000 chars
        response = self.client.post('/api/convert',
            {'source_language': 'python', 'target_language': 'java', 'code': huge_code},
            format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('50,000', response.data['error'])

    def test_convert_missing_fields(self):
        response = self.client.post('/api/convert',
            {'source_language': 'python'},
            format='json')
        self.assertEqual(response.status_code, 400)


@override_settings(AXES_ENABLED=False)
class RunCodeTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    @patch('converter.views._pick_compiler', return_value='cpython-3.12.0')
    @patch('converter.views.http_requests.post')
    def test_run_no_auth_required(self, mock_post, mock_compiler):
        mock_post.return_value.raise_for_status = lambda: None
        mock_post.return_value.json.return_value = {
            'status': '0', 'program_output': '1\n', 'compiler_output': '', 'program_error': ''
        }
        response = self.client.post('/api/run/',
            {'language': 'python', 'code': 'print(1)'},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['code'], 0)

    def test_run_unsupported_language(self):
        response = self.client.post('/api/run/',
            {'language': 'ruby', 'code': 'puts "hi"'},
            format='json')
        self.assertEqual(response.status_code, 400)

    def test_run_empty_code(self):
        response = self.client.post('/api/run/',
            {'language': 'python', 'code': '   '},
            format='json')
        self.assertEqual(response.status_code, 400)

    def test_run_code_too_long(self):
        huge = 'x = 1\n' * 2_000  # > 10,000 chars
        response = self.client.post('/api/run/',
            {'language': 'python', 'code': huge},
            format='json')
        self.assertEqual(response.status_code, 400)


@override_settings(AXES_ENABLED=False)
class VisualizeCodeTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='visual_user', email='visual@example.com', password='Test1234!')
        self.client = _make_authed_client(self.user)

    def test_visualize_requires_auth(self):
        response = APIClient().post('/api/visualize',
            {'language': 'python', 'code': SAMPLE_PYTHON},
            format='json')
        self.assertEqual(response.status_code, 401)

    def test_visualize_python_returns_timeline(self):
        code = 'total = 0\nfor n in [1, 2, 3]:\n    total = total + n\nprint(total)\n'
        response = self.client.post('/api/visualize',
            {'language': 'python', 'code': code},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['language'], 'python')
        self.assertIn('loops', response.data['concepts'])
        self.assertIn('variables', response.data['concepts'])
        self.assertGreaterEqual(len(response.data['steps']), 4)
        self.assertEqual(response.data['steps'][0]['line'], 1)
        self.assertIn('visual', response.data['steps'][0])

    def test_visualize_c_family_detects_output_and_conditionals(self):
        code = 'int x = 3;\nif (x > 2) {\n  printf("%d", x);\n}\n'
        response = self.client.post('/api/visualize',
            {'language': 'c', 'code': code},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('conditionals', response.data['concepts'])
        self.assertIn('output', response.data['concepts'])

    def test_visualize_validates_language_and_code(self):
        bad_lang = self.client.post('/api/visualize',
            {'language': 'ruby', 'code': 'puts 1'},
            format='json')
        self.assertEqual(bad_lang.status_code, 400)

        empty = self.client.post('/api/visualize',
            {'language': 'python', 'code': '   '},
            format='json')
        self.assertEqual(empty.status_code, 400)

    def test_visualize_code_too_long(self):
        huge = 'x = 1\n' * 4_000
        response = self.client.post('/api/visualize',
            {'language': 'python', 'code': huge},
            format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('20,000', response.data['error'])


@override_settings(AXES_ENABLED=False)
class SnippetTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='snippet_user', email='snip@example.com', password='Test1234!')
        self.authed = _make_authed_client(self.user)
        self.anon = APIClient()

    def test_create_snippet_requires_auth(self):
        response = self.anon.post('/api/snippets/', {
            'source_language': 'python', 'target_language': 'java',
            'input_code': SAMPLE_PYTHON, 'output_code': SAMPLE_JAVA, 'engine': 'ai',
        }, format='json')
        self.assertEqual(response.status_code, 401)

    def test_create_and_get_snippet(self):
        create_resp = self.authed.post('/api/snippets/', {
            'source_language': 'python', 'target_language': 'java',
            'input_code': SAMPLE_PYTHON, 'output_code': SAMPLE_JAVA, 'engine': 'ai',
        }, format='json')
        self.assertEqual(create_resp.status_code, 201)
        slug = create_resp.data['slug']

        # Public GET — no auth required
        get_resp = self.anon.get(f'/api/snippets/{slug}/')
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.data['source_language'], 'python')

    def test_create_snippet_validates_language_and_size(self):
        response = self.authed.post('/api/snippets/', {
            'source_language': 'ruby', 'target_language': 'java',
            'input_code': 'puts 1', 'output_code': SAMPLE_JAVA, 'engine': 'ai',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_get_nonexistent_snippet(self):
        response = self.anon.get('/api/snippets/does-not-exist/')
        self.assertEqual(response.status_code, 404)


@override_settings(AXES_ENABLED=False)
class ConversionHistoryTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='hist_user', email='hist@example.com', password='Test1234!')
        self.client = _make_authed_client(self.user)

    def test_history_requires_auth(self):
        anon = APIClient()
        response = anon.get('/api/convert/history')
        self.assertEqual(response.status_code, 401)

    def test_history_empty(self):
        response = self.client.get('/api/convert/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
