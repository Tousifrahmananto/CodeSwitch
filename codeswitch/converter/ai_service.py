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

import requests

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
    'gemini': 'gemini-2.0-flash-lite',
    'openai': 'gpt-3.5-turbo',
    'groq':   'llama-3.1-8b-instant',
}

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


def _call_gemini(api_key: str, model: str, user_prompt: str) -> str:
    """Call the Google Gemini generateContent REST API."""
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{model}:generateContent?key={api_key}'
    )
    payload = {
        'system_instruction': {'parts': [{'text': _SYSTEM_PROMPT}]},
        'contents': [{'parts': [{'text': user_prompt}]}],
        'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 4096},
    }
    resp = requests.post(url, json=payload, timeout=25)
    resp.raise_for_status()
    data = resp.json()
    return data['candidates'][0]['content']['parts'][0]['text']


def _call_openai_compatible(api_key: str, base_url: str, model: str, user_prompt: str) -> str:
    """Call any OpenAI-compatible /chat/completions endpoint."""
    url = f'{base_url.rstrip("/")}/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': _SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': 0.1,
        'max_tokens': 4096,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=25)
    resp.raise_for_status()
    return resp.json()['choices'][0]['message']['content']


# HTTP status codes that mean "this key is exhausted/invalid — try the next one"
_ROTATE_STATUSES = {401, 403, 429}


def ai_convert_code(source_lang: str, target_lang: str, code: str, user_key: str = None) -> dict:
    """
    Convert code using an AI model.

    Tries each configured API key in order (user_key if provided, then
    AI_API_KEY, AI_API_KEY_2, AI_API_KEY_3). On a rate-limit (429) or
    auth error (401/403) it moves to the next key. On the last key it
    retries once after a 3-second wait before giving up.

    Returns:
        {'success': True,  'output': str, 'engine': 'ai'}
        {'success': False, 'error': str}

    NOTE: Detailed errors are logged server-side for debugging.
    Clients receive generic error messages for security.
    """
    api_keys = ([user_key.strip()] if user_key and user_key.strip() else []) + _get_api_keys()
    if not api_keys:
        logger.warning("AI_API_KEY not configured in .env")
        return {'success': False, 'error': 'AI service unavailable'}

    provider = _get('AI_PROVIDER', 'gemini').lower().strip()
    model    = _get('AI_MODEL', _DEFAULT_MODELS.get(provider, 'gemini-2.0-flash-lite')).strip()
    base_url = _get('AI_BASE_URL', _BASE_URLS.get(provider, _BASE_URLS['openai']))

    user_prompt = f'Convert the following {source_lang} code to {target_lang}.\n\n{code}'

    last_error_detail = 'All API keys exhausted.'

    for key_index, api_key in enumerate(api_keys):
        is_last_key = (key_index == len(api_keys) - 1)
        attempts = 2 if is_last_key else 1  # retry once only on the last key

        for attempt in range(attempts):
            try:
                if provider == 'gemini':
                    raw = _call_gemini(api_key, model, user_prompt)
                else:
                    raw = _call_openai_compatible(api_key, base_url, model, user_prompt)

                output = _strip_markdown(raw)
                return {'success': True, 'output': output, 'engine': 'ai'}

            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                last_error_detail = f'HTTP {status} from {provider} (key #{key_index + 1}): {exc}'
                logger.error(last_error_detail)

                if status in _ROTATE_STATUSES:
                    if is_last_key and attempt == 0:
                        # Last key, first attempt — retry immediately
                        continue
                    # Move on to the next key
                    break
                else:
                    # Non-quota error (e.g. 500) — no point trying other keys
                    logger.error(f"Non-retryable AI service error: {last_error_detail}")
                    return {'success': False, 'error': 'AI service temporarily unavailable'}

            except Exception as exc:
                last_error_detail = f'Conversion service error (key #{key_index + 1}): {type(exc).__name__}: {exc}'
                logger.error(last_error_detail)
                break  # unexpected error — try next key

    # All keys exhausted — return generic error to client, detailed error logged
    logger.error(f"All AI conversion keys exhausted: {last_error_detail}")
    return {'success': False, 'error': 'AI service unavailable. Please try again later.'}


_EXPLAIN_SYSTEM_PROMPT = (
    'You are a programming tutor. Your job is to explain, in plain English, '
    'the key differences between a piece of code in one language and its translation '
    'to another language. Focus on concepts that are educational for a student learning '
    'the target language: highlight important syntax differences, idioms, or constructs '
    'that changed. Be concise (3-6 sentences). Do not repeat the code.'
)


def ai_explain_code(source_lang: str, target_lang: str, input_code: str, output_code: str, user_key: str = None) -> dict:
    """
    Explain the key differences between source code and its translation.

    Returns:
        {'success': True,  'explanation': str}
        {'success': False, 'error': str}

    NOTE: Detailed errors logged server-side, generic messages sent to clients.
    """
    api_keys = ([user_key.strip()] if user_key and user_key.strip() else []) + _get_api_keys()
    if not api_keys:
        logger.warning("AI_API_KEY not configured in .env, cannot explain code")
        return {'success': False, 'error': 'AI service unavailable'}

    provider = _get('AI_PROVIDER', 'gemini').lower().strip()
    model    = _get('AI_MODEL', _DEFAULT_MODELS.get(provider, 'gemini-2.0-flash-lite')).strip()
    base_url = _get('AI_BASE_URL', _BASE_URLS.get(provider, _BASE_URLS['openai']))

    user_prompt = (
        f'Here is a {source_lang} program and its {target_lang} translation. '
        f'Explain the key differences to a student learning {target_lang}.\n\n'
        f'--- {source_lang} (original) ---\n{input_code}\n\n'
        f'--- {target_lang} (translated) ---\n{output_code}'
    )

    last_error_detail = 'All API keys exhausted.'

    for key_index, api_key in enumerate(api_keys):
        is_last_key = (key_index == len(api_keys) - 1)
        attempts = 2 if is_last_key else 1

        for attempt in range(attempts):
            try:
                if provider == 'gemini':
                    url = (
                        f'https://generativelanguage.googleapis.com/v1beta/models/'
                        f'{model}:generateContent?key={api_key}'
                    )
                    payload = {
                        'system_instruction': {'parts': [{'text': _EXPLAIN_SYSTEM_PROMPT}]},
                        'contents': [{'parts': [{'text': user_prompt}]}],
                        'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 512},
                    }
                    resp = requests.post(url, json=payload, timeout=25)
                    resp.raise_for_status()
                    raw = resp.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    url = f'{base_url.rstrip("/")}/chat/completions'
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json',
                    }
                    payload = {
                        'model': model,
                        'messages': [
                            {'role': 'system', 'content': _EXPLAIN_SYSTEM_PROMPT},
                            {'role': 'user', 'content': user_prompt},
                        ],
                        'temperature': 0.3,
                        'max_tokens': 512,
                    }
                    resp = requests.post(url, json=payload, headers=headers, timeout=25)
                    resp.raise_for_status()
                    raw = resp.json()['choices'][0]['message']['content']

                return {'success': True, 'explanation': raw.strip()}

            except requests.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else None
                last_error_detail = f'HTTP {status_code} from {provider} (key #{key_index + 1}): {exc}'
                logger.error(last_error_detail)

                if status_code in _ROTATE_STATUSES:
                    if is_last_key and attempt == 0:
                        continue
                    break
                else:
                    logger.error(f"Non-retryable explanation service error: {last_error_detail}")
                    return {'success': False, 'error': 'AI service temporarily unavailable'}

            except Exception as exc:
                last_error_detail = f'Code explanation error (key #{key_index + 1}): {type(exc).__name__}: {exc}'
                logger.error(last_error_detail)
                break

    logger.error(f"All explanation service keys exhausted: {last_error_detail}")
    return {'success': False, 'error': 'AI service unavailable. Please try again later.'}
