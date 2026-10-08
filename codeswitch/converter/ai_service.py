"""
CodeSwitch AI Conversion Service
---------------------------------
Uses an LLM to convert code between programming languages.

Supported providers (set via .env):
  gemini  → Google Gemini  (free tier at aistudio.google.com/app/apikey)
  openai  → OpenAI         (platform.openai.com)
  groq    → Groq            (free tier at console.groq.com)

Required .env settings:
  AI_PROVIDER  = gemini | openai | groq    (default: gemini)
  AI_API_KEY   = <your primary API key>
  AI_API_KEY_2 = <fallback key #2>         (optional)
  AI_API_KEY_3 = <fallback key #3>         (optional)
  AI_MODEL     = <model name>              (optional, sensible defaults applied)
  AI_BASE_URL  = <custom endpoint>         (optional, overrides provider default)

If a key hits a rate limit (HTTP 429) or auth error (HTTP 401/403),
the service automatically retries with the next available key.
"""

import os
import re
import logging
import time
from .http_client import request_json

import requests
from codeswitch.observability import dependency_timer

try:
    from decouple import config as _decouple_config
    _DECOUPLE_AVAILABLE = True
except ImportError:
    _DECOUPLE_AVAILABLE = False

# Setup logging for secure error tracking
logger = logging.getLogger(__name__)


def _get(key: str, default: str = '') -> str:
    """Read config from .env via python-decouple, falling back to os.environ."""
    if _DECOUPLE_AVAILABLE:
        return _decouple_config(key, default=default)
    return os.environ.get(key, default)


# ── Default models per provider ────────────────────────────────────────────────
_DEFAULT_MODELS = {
    'gemini': 'gemini-3.1-flash-lite',
    'openai': 'gpt-3.5-turbo',
    'groq':   'openai/gpt-oss-20b',
}


def _get_model(provider: str) -> str:
    default = _DEFAULT_MODELS.get(provider, _DEFAULT_MODELS['gemini'])
    model = _get('AI_MODEL', default).strip() or default
    # Groq retired this model on 2026-08-16; migrate existing deployment settings.
    if provider == 'groq' and model == 'llama-3.1-8b-instant':
        return _DEFAULT_MODELS['groq']
    if provider == 'gemini' and model in {
        'gemini-2.0-flash', 'gemini-2.0-flash-lite',
        'gemini-2.0-flash-001', 'gemini-2.0-flash-lite-001',
    }:
        return _DEFAULT_MODELS['gemini']
    return model

# ── OpenAI-compatible base URLs ────────────────────────────────────────────────
_BASE_URLS = {
    'openai': 'https://api.openai.com/v1',
    'groq':   'https://api.groq.com/openai/v1',
}

_SYSTEM_PROMPT = (
    'You are an expert code translator. Your only job is to convert source code '
    'from one programming language to another. '
    'Return ONLY the converted code. Do NOT include any explanation, comments about '
    'the conversion, or markdown formatting. Do NOT wrap the output in code fences. '
    'Preserve the original logic exactly. Use idiomatic style of the target language.'
)


def _strip_markdown(text: str) -> str:
    """Remove markdown code fences that some models add despite instructions."""
    text = text.strip()
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    return text.strip()


def _get_api_keys() -> list:
    """Return a list of all configured API keys, filtering out blanks."""
    keys = []
    for slot in ('AI_API_KEY', 'AI_API_KEY_2', 'AI_API_KEY_3'):
        k = _get(slot, '').strip()
        if k:
            keys.append(k)
    return keys


class AIResponseError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__('AI returned an empty or incomplete response.')


def _response_text(data, provider):
    try:
        if provider == 'gemini':
            choice = data['candidates'][0]
            reason = choice.get('finishReason')
            complete = reason == 'STOP'
            text = ''.join(part['text'] for part in choice['content']['parts'])
        else:
            choice = data['choices'][0]
            reason = choice.get('finish_reason')
            complete = reason == 'stop'
            text = choice['message']['content']
        if not complete:
            raise AIResponseError('ai_incomplete_response' if reason else 'ai_invalid_response')
        if not isinstance(text, str) or not _strip_markdown(text):
            raise AIResponseError('ai_invalid_response')
        return text
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise AIResponseError('ai_invalid_response') from exc


def _call_gemini(api_key, model, user_prompt, timeout, system_prompt, temperature, max_tokens, deadline):
    """Call the Google Gemini generateContent REST API."""
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{model}:generateContent?key={api_key}'
    )
    payload = {
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': [{'parts': [{'text': user_prompt}]}],
        'generationConfig': {'temperature': temperature, 'maxOutputTokens': max_tokens},
    }
    with dependency_timer('ai_gemini'):
        data = request_json('post', url, deadline, json=payload, timeout=timeout)
    return _response_text(data, 'gemini')


def _call_openai_compatible(api_key, base_url, model, user_prompt, timeout, system_prompt, temperature, max_tokens, deadline):
    """Call any OpenAI-compatible /chat/completions endpoint."""
    url = f'{base_url.rstrip("/")}/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    with dependency_timer('ai_openai_compatible'):
        data = request_json('post', url, deadline, json=payload, headers=headers, timeout=timeout)
    return _response_text(data, 'openai')


# HTTP status codes that mean "this key is exhausted/invalid — try the next one"
_ROTATE_STATUSES = {401, 403, 429}


AI_ATTEMPT_BUDGET = 20
AI_CONNECT_TIMEOUT = 3
AI_READ_TIMEOUT = 10


def _generate_text(user_prompt, system_prompt, temperature, max_tokens, user_key):
    provider = _get('AI_PROVIDER', 'gemini').lower().strip()
    api_keys = ([user_key.strip()] if user_key and user_key.strip() else []) + _get_api_keys()
    if not api_keys:
        return {'success': False, 'error': 'AI service is not configured.', 'ai_provider': provider, 'ai_error_code': 'ai_not_configured'}
    model = _get_model(provider)
    base_url = _get('AI_BASE_URL', _BASE_URLS.get(provider, _BASE_URLS['openai']))
    deadline = time.monotonic() + AI_ATTEMPT_BUDGET
    for key_index, api_key in enumerate(api_keys):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {'success': False, 'error': 'AI request timed out.', 'ai_provider': provider, 'ai_error_code': 'ai_timeout'}
        connect = min(AI_CONNECT_TIMEOUT, remaining / 2)
        timeout = (connect, min(AI_READ_TIMEOUT, remaining - connect))
        try:
            if provider == 'gemini':
                text = _call_gemini(api_key, model, user_prompt, timeout, system_prompt, temperature, max_tokens, deadline)
            else:
                text = _call_openai_compatible(api_key, base_url, model, user_prompt, timeout, system_prompt, temperature, max_tokens, deadline)
            if time.monotonic() >= deadline:
                return {'success': False, 'error': 'AI request timed out.', 'ai_provider': provider, 'ai_error_code': 'ai_timeout'}
            return {'success': True, 'text': text}
        except AIResponseError as exc:
            return {'success': False, 'error': str(exc), 'ai_provider': provider, 'ai_error_code': exc.code}
        except requests.Timeout:
            return {'success': False, 'error': 'AI request timed out.', 'ai_provider': provider, 'ai_error_code': 'ai_timeout'}
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            logger.warning('AI HTTP %s from %s (key slot %s)', status, provider, key_index + 1)
            if status in _ROTATE_STATUSES:
                continue
            return {'success': False, 'error': 'AI service temporarily unavailable.', 'ai_provider': provider, 'ai_error_code': 'ai_unavailable'}
        except (ValueError, KeyError, TypeError):
            return {'success': False, 'error': 'AI returned an invalid response.', 'ai_provider': provider, 'ai_error_code': 'ai_invalid_response'}
        except requests.RequestException:
            return {'success': False, 'error': 'AI service temporarily unavailable.', 'ai_provider': provider, 'ai_error_code': 'ai_unavailable'}
        except Exception as exc:
            logger.error('AI request failed: %s', type(exc).__name__)
            return {'success': False, 'error': 'AI service temporarily unavailable.', 'ai_provider': provider, 'ai_error_code': 'ai_unavailable'}
    return {'success': False, 'error': 'AI keys are invalid or their quota is exhausted.', 'ai_provider': provider, 'ai_error_code': 'ai_quota_exhausted'}


def ai_convert_code(source_lang: str, target_lang: str, code: str, user_key: str = None) -> dict:
    prompt = f'Convert the following {source_lang} code to {target_lang}.\n\n{code}'
    result = _generate_text(prompt, _SYSTEM_PROMPT, 0.1, 4096, user_key)
    if not result['success']:
        return result
    return {'success': True, 'output': _strip_markdown(result['text']), 'engine': 'ai'}


_EXPLAIN_SYSTEM_PROMPT = (
    'You are a programming tutor. Your job is to explain, in plain English, '
    'the key differences between a piece of code in one language and its translation '
    'to another language. Focus on concepts that are educational for a student learning '
    'the target language: highlight important syntax differences, idioms, or constructs '
    'that changed. Be concise (3-6 sentences). Do not repeat the code.'
)


def ai_explain_code(source_lang: str, target_lang: str, input_code: str, output_code: str, user_key: str = None) -> dict:
    prompt = (
        f'Here is a {source_lang} program and its {target_lang} translation. '
        f'Explain the key differences to a student learning {target_lang}.\n\n'
        f'--- {source_lang} (original) ---\n{input_code}\n\n'
        f'--- {target_lang} (translated) ---\n{output_code}'
    )
    result = _generate_text(prompt, _EXPLAIN_SYSTEM_PROMPT, 0.3, 512, user_key)
    if not result['success']:
        return result
    return {'success': True, 'explanation': result['text'].strip()}
