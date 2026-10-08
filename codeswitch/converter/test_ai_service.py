from unittest import TestCase
from unittest.mock import Mock, patch

from converter import ai_service


class GroqModelMigrationTests(TestCase):
    def config(self, key, default=''):
        return {
            'AI_PROVIDER': 'groq',
            'AI_MODEL': 'llama-3.1-8b-instant',
            'AI_API_KEY': 'test-key',
        }.get(key, default)

    @patch.object(ai_service, '_get')
    @patch.object(ai_service, 'requests')
    def test_both_helpers_use_replacement_for_retired_model(self, requests, config):
        config.side_effect = self.config
        response = Mock()
        response.json.return_value = {'choices': [{'message': {'content': 'result'}}]}
        requests.post.return_value = response

        conversion = ai_service.ai_convert_code('python', 'c', 'print(1)')
        explanation = ai_service.ai_explain_code('python', 'c', 'print(1)', 'puts("1");')

        self.assertTrue(conversion['success'])
        self.assertTrue(explanation['success'])
        self.assertEqual(requests.post.call_count, 2)
        for call in requests.post.call_args_list:
            self.assertEqual(call.kwargs['json']['model'], 'openai/gpt-oss-20b')

    def test_other_model_settings_are_preserved(self):
        with patch.object(ai_service, '_get', return_value='custom-model'):
            self.assertEqual(ai_service._get_model('groq'), 'custom-model')
        with patch.object(ai_service, '_get', return_value='llama-3.1-8b-instant'):
            self.assertEqual(ai_service._get_model('openai'), 'llama-3.1-8b-instant')

    def test_groq_default_is_current_model(self):
        with patch.object(ai_service, '_get', side_effect=lambda key, default='': default):
            self.assertEqual(ai_service._get_model('groq'), 'openai/gpt-oss-20b')
