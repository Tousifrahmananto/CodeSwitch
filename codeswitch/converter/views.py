import threading
import time
import requests as http_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers
from .services import convert_code
from .ai_service import ai_explain_code
from .models import ConversionHistory, SharedSnippet
from .throttles import (
    AIBurstThrottle, AISustainedThrottle, RunCodeAnonThrottle,
    RunCodeUserThrottle, SnippetIPThrottle, SnippetCreateThrottle,
    HistoryReadThrottle, RunCodeAnonSustainedThrottle,
    RunCodeUserSustainedThrottle, VerifyBurstThrottle,
    VerifySustainedThrottle, VisualizerBurstThrottle,
    VisualizerSustainedThrottle,
)
from .serializers import SharedSnippetCreateSerializer
from .visualizer import build_visualization
from codeswitch.observability import dependency_timer, record_conversion
from codeswitch.pagination import OptionalPageNumberPagination

# ── Wandbox compiler list — fetched once, cached for the process lifetime ─────
_wandbox_compilers = None
_wandbox_compilers_fetched_at = 0.0
_wandbox_lock = threading.Lock()
_WANDBOX_CACHE_TTL = 3600

# Prefix used to identify each language's compiler in the Wandbox list
_LANG_PREFIX = {
    'python':     'cpython-',
    'java':       'openjdk-',
    'javascript': 'nodejs-',
    'c':          'gcc-',
    'cpp':        'gcc-',
}
# Extra compiler flags (GCC needs -x c to compile as C rather than C++)
_LANG_OPTIONS = {
    'c': '-x c -std=c11',
}

EXECUTION_LANGUAGES = {'python', 'c', 'java', 'javascript', 'cpp'}
MAX_EXECUTION_CODE_LENGTH = 10_000
MAX_EXECUTION_STDIN_LENGTH = 10_000
MAX_EXECUTION_OUTPUT_LENGTH = 100_000


class CodeExecutionServiceError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_wandbox_compilers():
    global _wandbox_compilers, _wandbox_compilers_fetched_at
    with _wandbox_lock:
        if _wandbox_compilers is not None and time.monotonic() - _wandbox_compilers_fetched_at < _WANDBOX_CACHE_TTL:
            return _wandbox_compilers
        try:
            with dependency_timer('wandbox_list'):
                resp = http_requests.get('https://wandbox.org/api/list.json', timeout=10)
                resp.raise_for_status()
                _wandbox_compilers = resp.json()
                _wandbox_compilers_fetched_at = time.monotonic()
        except Exception:
            # Keep stale successful data; otherwise retry on the next request.
            return _wandbox_compilers or []
        return _wandbox_compilers or []


def _pick_compiler(language):
    """Return the best available Wandbox compiler name for the given language."""
    prefix = _LANG_PREFIX.get(language)
    if not prefix:
        return None
    compilers = _get_wandbox_compilers()
    names = [c['name'] for c in compilers if c['name'].startswith(prefix)]
    if not names:
        return None
    # Prefer specific version numbers over -head (more stable)
    stable = [n for n in names if 'head' not in n]
    return stable[-1] if stable else names[-1]


def _execute_code(language, code, stdin=''):
    """Execute already-validated code through Wandbox and normalize its result."""
    compiler = _pick_compiler(language)
    if not compiler:
        raise CodeExecutionServiceError(
            'Could not find a compiler. The execution service may be temporarily unavailable.',
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    options = _LANG_OPTIONS.get(language, '')
    try:
        with dependency_timer('wandbox_compile'):
            resp = http_requests.post(
                'https://wandbox.org/api/compile.json',
                json={'compiler': compiler, 'code': code, 'options': options, 'stdin': stdin},
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
    except http_requests.Timeout as exc:
        raise CodeExecutionServiceError(
            'Execution timed out.', status.HTTP_504_GATEWAY_TIMEOUT
        ) from exc
    except (http_requests.RequestException, ValueError) as exc:
        raise CodeExecutionServiceError(
            'Execution service temporarily unavailable.',
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc

    try:
        exit_code = int(result.get('status', -1))
    except (TypeError, ValueError) as exc:
        raise CodeExecutionServiceError(
            'Execution service returned an invalid response.',
            status.HTTP_502_BAD_GATEWAY,
        ) from exc
    stdout = (result.get('program_output') or '')[:MAX_EXECUTION_OUTPUT_LENGTH]
    compile_err = (result.get('compiler_output') or '').strip()
    runtime_err = (result.get('program_error') or '').strip()
    stderr = '\n'.join(part for part in (compile_err, runtime_err) if part)

    return {
        'stdout': stdout,
        'stderr': stderr[:MAX_EXECUTION_OUTPUT_LENGTH],
        'code': exit_code,
    }


def _normalize_program_output(value):
    """Ignore platform newline differences and trailing horizontal whitespace."""
    normalized = value.replace('\r\n', '\n').replace('\r', '\n')
    return '\n'.join(line.rstrip() for line in normalized.split('\n')).rstrip('\n')


class ConvertCodeView(APIView):
    """
    POST /api/convert
    Body: { source_language, target_language, code }
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIBurstThrottle, AISustainedThrottle]

    VALID_LANGUAGES = {'python', 'c', 'java', 'javascript', 'cpp'}
    MAX_CODE_LENGTH = 50_000

    def post(self, request):
        source = request.data.get('source_language', '').lower()
        target = request.data.get('target_language', '').lower()
        code = request.data.get('code', '')

        if not source or not target or not code:
            return Response(
                {'error': 'source_language, target_language, and code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if source not in self.VALID_LANGUAGES or target not in self.VALID_LANGUAGES:
            return Response(
                {'error': f'Languages must be one of: {", ".join(sorted(self.VALID_LANGUAGES))}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(code) > self.MAX_CODE_LENGTH:
            return Response(
                {'error': f'Code must be under {self.MAX_CODE_LENGTH:,} characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Strip null bytes that could cause issues in downstream processing
        code = code.replace('\x00', '')

        user_key = request.headers.get('X-User-Api-Key') or None
        result = convert_code(source, target, code, user_key=user_key)

        if result['success']:
            record_conversion(result.get('engine', 'rules'), 'success')
            # Save to history
            ConversionHistory.objects.create(
                user=request.user,
                source_language=source,
                target_language=target,
                input_code=code,
                output_code=result['output'],
            )
            return Response(
                {'output': result['output'], 'engine': result.get('engine', 'rules')},
                status=status.HTTP_200_OK
            )
        else:
            record_conversion(result.get('engine', 'unknown'), 'error')
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)


class ConversionHistoryView(APIView):
    """GET /api/convert/history — List the user's past conversions."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [HistoryReadThrottle]

    def get(self, request):
        queryset = ConversionHistory.objects.filter(user=request.user).order_by('-timestamp')
        paginator = OptionalPageNumberPagination()
        history = paginator.paginate_queryset(queryset, request, view=self)
        paginated = history is not None
        if history is None:
            history = queryset[:50]
        data = [
            {
                'id': h.id,
                'source_language': h.source_language,
                'target_language': h.target_language,
                'input_code': h.input_code,
                'output_code': h.output_code,
                'timestamp': h.timestamp,
            }
            for h in history
        ]
        return paginator.get_paginated_response(data) if paginated else Response(data)


class CreateSnippetView(APIView):
    """POST /api/snippets/ — Save a conversion as a shareable snippet."""
    permission_classes = [IsAuthenticated]
    throttle_classes = [SnippetCreateThrottle]

    def post(self, request):
        serializer = SharedSnippetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snippet = serializer.save()
        return Response({'slug': str(snippet.slug)}, status=status.HTTP_201_CREATED)


class GetSnippetView(APIView):
    """GET /api/snippets/<slug>/ — Retrieve a shared snippet (no auth required)."""
    permission_classes = [AllowAny]
    throttle_classes = [SnippetIPThrottle]

    def get(self, request, slug):
        try:
            snippet = SharedSnippet.objects.get(slug=slug)
        except SharedSnippet.DoesNotExist:
            return Response({'error': 'Snippet not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'source_language': snippet.source_language,
            'target_language': snippet.target_language,
            'input_code': snippet.input_code,
            'output_code': snippet.output_code,
            'engine': snippet.engine,
            'created_at': snippet.created_at,
        })


class RunCodeView(APIView):
    """
    POST /api/run/
    Body: { language, code }
    Public endpoint — no authentication required.
    Proxies code execution to Wandbox, picking the best available compiler.
    """
    permission_classes = [AllowAny]
    throttle_classes = [
        RunCodeAnonThrottle, RunCodeAnonSustainedThrottle,
        RunCodeUserThrottle, RunCodeUserSustainedThrottle,
    ]
    SUPPORTED = EXECUTION_LANGUAGES
    MAX_CODE_LENGTH = MAX_EXECUTION_CODE_LENGTH
    MAX_STDIN_LENGTH = MAX_EXECUTION_STDIN_LENGTH

    def post(self, request):
        language = request.data.get('language', '').lower().strip()
        code = request.data.get('code', '')
        stdin = request.data.get('stdin', '')

        if language not in self.SUPPORTED:
            return Response(
                {'error': f'Unsupported language: {language}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not code.strip():
            return Response({'error': 'No code provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(code) > self.MAX_CODE_LENGTH:
            return Response(
                {'error': f'Code must be under {self.MAX_CODE_LENGTH:,} characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(stdin) > self.MAX_STDIN_LENGTH:
            return Response(
                {'error': f'Standard input must be under {self.MAX_STDIN_LENGTH:,} characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = _execute_code(language, code, stdin)
        except CodeExecutionServiceError as exc:
            return Response({'error': exc.message}, status=exc.status_code)

        return Response(result)


class VerifyConversionView(APIView):
    """
    POST /api/verify
    Execute source and converted code with identical stdin and compare behavior.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [VerifyBurstThrottle, VerifySustainedThrottle]

    def post(self, request):
        source_language = request.data.get('source_language', '').lower().strip()
        target_language = request.data.get('target_language', '').lower().strip()
        source_code = request.data.get('source_code', '')
        target_code = request.data.get('target_code', '')
        stdin = request.data.get('stdin', '')

        if source_language not in EXECUTION_LANGUAGES or target_language not in EXECUTION_LANGUAGES:
            return Response(
                {'error': 'Source and target languages must support execution.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if source_language == target_language:
            return Response(
                {'error': 'Source and target languages must differ.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not source_code.strip() or not target_code.strip():
            return Response(
                {'error': 'Source code and converted code are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(source_code) > MAX_EXECUTION_CODE_LENGTH or len(target_code) > MAX_EXECUTION_CODE_LENGTH:
            return Response(
                {'error': f'Each code sample must be under {MAX_EXECUTION_CODE_LENGTH:,} characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(stdin) > MAX_EXECUTION_STDIN_LENGTH:
            return Response(
                {'error': f'Standard input must be under {MAX_EXECUTION_STDIN_LENGTH:,} characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            source_result = _execute_code(source_language, source_code, stdin)
            target_result = _execute_code(target_language, target_code, stdin)
        except CodeExecutionServiceError as exc:
            return Response({'error': exc.message}, status=exc.status_code)

        source_succeeded = source_result['code'] == 0
        target_succeeded = target_result['code'] == 0
        stdout_match = (
            _normalize_program_output(source_result['stdout'])
            == _normalize_program_output(target_result['stdout'])
        )
        exit_code_match = source_result['code'] == target_result['code']
        verified = source_succeeded and target_succeeded and stdout_match

        if verified:
            result_status = 'match'
            summary = 'Both programs completed successfully and produced matching output.'
        elif not source_succeeded:
            result_status = 'source_error'
            summary = 'The original program failed, so the conversion could not be verified.'
        elif not target_succeeded:
            result_status = 'target_error'
            summary = 'The converted program failed to compile or run.'
        else:
            result_status = 'mismatch'
            summary = 'Both programs ran successfully, but their output differs.'

        return Response({
            'verified': verified,
            'status': result_status,
            'summary': summary,
            'source': source_result,
            'target': target_result,
            'comparison': {
                'stdout_match': stdout_match,
                'exit_code_match': exit_code_match,
            },
        })


class ExplainCodeView(APIView):
    """
    POST /api/explain/
    Body: { input_code, output_code, source_language, target_language }
    Returns a plain-English explanation of the conversion differences.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [AIBurstThrottle, AISustainedThrottle]

    VALID_LANGUAGES = {'python', 'c', 'java', 'javascript', 'cpp'}
    MAX_CODE_LENGTH = 50_000

    def post(self, request):
        source = request.data.get('source_language', '').lower()
        target = request.data.get('target_language', '').lower()
        input_code = request.data.get('input_code', '')
        output_code = request.data.get('output_code', '')

        if not source or not target or not input_code or not output_code:
            return Response(
                {'error': 'source_language, target_language, input_code, and output_code are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if source not in self.VALID_LANGUAGES or target not in self.VALID_LANGUAGES:
            return Response(
                {'error': f'Languages must be one of: {", ".join(sorted(self.VALID_LANGUAGES))}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(input_code) > self.MAX_CODE_LENGTH or len(output_code) > self.MAX_CODE_LENGTH:
            return Response(
                {'error': f'Code must be under {self.MAX_CODE_LENGTH:,} characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = ai_explain_code(source, target, input_code, output_code,
                                  user_key=request.headers.get('X-User-Api-Key') or None)

        if result['success']:
            return Response({'explanation': result['explanation']}, status=status.HTTP_200_OK)
        else:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)


class VisualizeCodeView(APIView):
    """
    POST /api/visualize
    Body: { language, code }
    Returns a deterministic educational animation timeline.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [VisualizerBurstThrottle, VisualizerSustainedThrottle]

    def post(self, request):
        language = request.data.get('language', '')
        code = request.data.get('code', '')
        try:
            timeline = build_visualization(language, code)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(timeline, status=status.HTTP_200_OK)
