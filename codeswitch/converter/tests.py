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
class VerifyConversionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='verify_user', email='verify@example.com', password='Test1234!')
        self.client = _make_authed_client(self.user)
        self.payload = {
            'source_language': 'python',
            'target_language': 'javascript',
            'source_code': 'print(3)',
            'target_code': 'console.log(3);',
            'stdin': '',
        }

    def test_verify_requires_authentication(self):
        response = APIClient().post('/api/verify', self.payload, format='json')
        self.assertEqual(response.status_code, 401)

    @patch('converter.views._execute_code')
    def test_verify_matching_programs(self, mock_execute):
        mock_execute.side_effect = [
            {'stdout': '3\n', 'stderr': '', 'code': 0},
            {'stdout': '3\r\n', 'stderr': '', 'code': 0},
        ]
        response = self.client.post('/api/verify', self.payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['verified'])
        self.assertEqual(response.data['status'], 'match')
        self.assertTrue(response.data['comparison']['stdout_match'])
        self.assertEqual(mock_execute.call_count, 2)

    @patch('converter.views._execute_code')
    def test_verify_output_mismatch(self, mock_execute):
        mock_execute.side_effect = [
            {'stdout': '3\n', 'stderr': '', 'code': 0},
            {'stdout': '4\n', 'stderr': '', 'code': 0},
        ]
        response = self.client.post('/api/verify', self.payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['verified'])
        self.assertEqual(response.data['status'], 'mismatch')
        self.assertFalse(response.data['comparison']['stdout_match'])

    @patch('converter.views._execute_code')
    def test_verify_converted_program_failure(self, mock_execute):
        mock_execute.side_effect = [
            {'stdout': '3\n', 'stderr': '', 'code': 0},
            {'stdout': '', 'stderr': 'compile error', 'code': 1},
        ]
        response = self.client.post('/api/verify', self.payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['verified'])
        self.assertEqual(response.data['status'], 'target_error')
        self.assertEqual(response.data['target']['stderr'], 'compile error')

    def test_verify_validates_payload(self):
        payload = {**self.payload, 'target_code': ''}
        response = self.client.post('/api/verify', payload, format='json')
        self.assertEqual(response.status_code, 400)


@override_settings(AXES_ENABLED=False, PYTHON_EXECUTION_TRACING_ENABLED=True)
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
        self.assertEqual(response.data['mode'], 'execution_trace')
        self.assertIn('loops', response.data['concepts'])
        self.assertIn('variables', response.data['concepts'])
        self.assertGreaterEqual(len(response.data['steps']), 4)
        self.assertGreaterEqual(len(response.data['trace']), 4)
        self.assertIn('frames', response.data['trace'][0])
        self.assertIn('heap', response.data['trace'][0])
        self.assertEqual(response.data['steps'][0]['line'], 1)
        self.assertIn('visual', response.data['steps'][0])
        self.assertIn('stack', response.data['steps'][0]['visual'])

    def test_visualize_python_uses_non_executing_concept_trace_by_default(self):
        with self.settings(PYTHON_EXECUTION_TRACING_ENABLED=False):
            response = self.client.post(
                '/api/visualize',
                {'language': 'python', 'code': 'print("safe")'},
                format='json',
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['mode'], 'concept_trace')
        self.assertNotIn('trace', response.data)

    def test_visualize_python_lists_and_dicts_create_heap_refs(self):
        code = 'items = [1, 2]\nstate = {"items": items}\nitems.append(3)\nprint(state)\n'
        response = self.client.post('/api/visualize',
            {'language': 'python', 'code': code},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['mode'], 'execution_trace')
        self.assertTrue(any(step['heap'] for step in response.data['trace']))
        self.assertTrue(any(
            isinstance(frame['variables'].get('items'), dict) and '$ref' in frame['variables']['items']
            for step in response.data['trace']
            for frame in step['frames']
        ))

    def test_visualize_python_runtime_error_returns_trace_and_error(self):
        code = 'x = 1\ny = 0\nprint(x / y)\n'
        response = self.client.post('/api/visualize',
            {'language': 'python', 'code': code},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['mode'], 'execution_trace')
        self.assertIn('error', response.data)
        self.assertIn('division by zero', response.data['error']['message'])
        self.assertTrue(response.data['trace'])
        self.assertTrue(any(step['event'] == 'exception' for step in response.data['trace']))

    def test_visualize_python_supports_safe_imports_and_classes(self):
        code = (
            'import math\n\n'
            'class Circle:\n'
            '    def __init__(self, radius):\n'
            '        self.radius = radius\n'
            '    def area(self):\n'
            '        return round(math.pi * self.radius ** 2, 2)\n\n'
            'shape = Circle(3)\n'
            'print(shape.area())\n'
        )
        response = self.client.post('/api/visualize',
            {'language': 'python', 'code': code},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['mode'], 'execution_trace')
        self.assertNotIn('error', response.data)
        self.assertTrue(any('28.27' in step['stdout'] for step in response.data['trace']))
        self.assertTrue(any(
            frame['name'] == 'area()'
            for step in response.data['trace']
            for frame in step['frames']
        ))

    def test_visualize_python_blocks_dangerous_imports(self):
        response = self.client.post('/api/visualize',
            {'language': 'python', 'code': 'import os\nprint(os.listdir("."))\n'},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['mode'], 'execution_trace')
        self.assertIn('error', response.data)
        self.assertIn("blocked", response.data['error']['message'])

    def test_visualize_python_return_negative_one_is_normal_return(self):
        code = 'def find(x):\n    if x > 0:\n        return x\n    return -1\n\nresult = find(0)\nprint(result)\n'
        response = self.client.post('/api/visualize',
            {'language': 'python', 'code': code},
            format='json')
        self.assertEqual(response.status_code, 200)
        return_steps = [step for step in response.data['steps'] if step['kind'] == 'return']
        self.assertTrue(return_steps)
        self.assertTrue(any(step['visual'].get('return_value') == '-1' for step in return_steps))
        self.assertFalse(any('error' in step['title'].lower() for step in return_steps))

    def test_visualize_c_family_detects_output_and_conditionals(self):
        code = 'int x = 3;\nif (x > 2) {\n  printf("%d", x);\n}\n'
        response = self.client.post('/api/visualize',
            {'language': 'c', 'code': code},
            format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['mode'], 'concept_trace')
        self.assertNotIn('trace', response.data)
        self.assertIn('conditionals', response.data['concepts'])
        self.assertIn('output', response.data['concepts'])
        self.assertTrue(response.data['steps'][-1]['visual']['stack'])
        self.assertTrue(response.data['steps'][-1]['visual']['output'])

    def test_visualize_all_non_python_languages_return_concept_traces(self):
        examples = {
            'javascript': 'let total = 1;\ntotal = total + 2;\nconsole.log(total);',
            'java': 'class Main {\n  public static void main(String[] args) {\n    int total = 3;\n    System.out.println(total);\n  }\n}',
            'cpp': '#include <iostream>\nint main() {\n  int total = 3;\n  std::cout << total;\n}',
            'c': '#include <stdio.h>\nint main() {\n  int total = 3;\n  printf("%d", total);\n}',
        }

        for language, code in examples.items():
            with self.subTest(language=language):
                response = self.client.post('/api/visualize',
                    {'language': language, 'code': code},
                    format='json')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['language'], language)
                self.assertEqual(response.data['mode'], 'concept_trace')
                self.assertGreaterEqual(len(response.data['steps']), 2)
                self.assertIn('variables', response.data['concepts'])
                self.assertIn('output', response.data['concepts'])
                self.assertTrue(response.data['steps'][-1]['visual']['stack'])
                self.assertTrue(response.data['steps'][-1]['visual']['output'])

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
