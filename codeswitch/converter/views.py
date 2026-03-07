import threading
import requests as http_requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers
from .services import convert_code
from .models import ConversionHistory, SharedSnippet

# ── Wandbox compiler list — fetched once, cached for the process lifetime ─────
_wandbox_compilers = None
_wandbox_lock = threading.Lock()

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


def _get_wandbox_compilers():
    global _wandbox_compilers
    with _wandbox_lock:
        if _wandbox_compilers is not None:
            return _wandbox_compilers
        try:
            resp = http_requests.get('https://wandbox.org/api/list.json', timeout=10)
            resp.raise_for_status()
            _wandbox_compilers = resp.json()
        except Exception:
            _wandbox_compilers = []
        return _wandbox_compilers


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


class ConvertCodeView(APIView):
    """
    POST /api/convert
    Body: { source_language, target_language, code }
    """
    permission_classes = [IsAuthenticated]

    VALID_LANGUAGES = {'python', 'c', 'java', 'javascript', 'cpp'}

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

        result = convert_code(source, target, code)

        if result['success']:
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
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)


class ConversionHistoryView(APIView):
    """GET /api/convert/history — List the user's past conversions."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = ConversionHistory.objects.filter(user=request.user)[:50]
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
        return Response(data)


class CreateSnippetView(APIView):
    """POST /api/snippets/ — Save a conversion as a shareable snippet."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        snippet = SharedSnippet.objects.create(
            source_language=data.get('source_language', ''),
            target_language=data.get('target_language', ''),
            input_code=data.get('input_code', ''),
            output_code=data.get('output_code', ''),
            engine=data.get('engine', 'ai'),
        )
        return Response({'slug': str(snippet.slug)}, status=status.HTTP_201_CREATED)


class GetSnippetView(APIView):
    """GET /api/snippets/<slug>/ — Retrieve a shared snippet (no auth required)."""
    permission_classes = [AllowAny]

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
    SUPPORTED = {'python', 'c', 'java', 'javascript', 'cpp'}

    def post(self, request):
        language = request.data.get('language', '').lower().strip()
        code = request.data.get('code', '')

        if language not in self.SUPPORTED:
            return Response(
                {'error': f'Unsupported language: {language}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not code.strip():
            return Response({'error': 'No code provided.'}, status=status.HTTP_400_BAD_REQUEST)

        compiler = _pick_compiler(language)
        if not compiler:
            return Response(
                {'error': 'Could not find a compiler. The execution service may be temporarily unavailable.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        options = _LANG_OPTIONS.get(language, '')
        try:
            resp = http_requests.post(
                'https://wandbox.org/api/compile.json',
                json={'compiler': compiler, 'code': code, 'options': options, 'stdin': ''},
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
        except http_requests.Timeout:
            return Response({'error': 'Execution timed out.'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except http_requests.RequestException as e:
            return Response(
                {'error': f'Execution service unavailable: {e}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        exit_code = int(result.get('status', -1))
        stdout = result.get('program_output', '')
        compile_err = (result.get('compiler_output') or '').strip()
        runtime_err = (result.get('program_error') or '').strip()
        stderr = '\n'.join(s for s in [compile_err, runtime_err] if s)

        return Response({'stdout': stdout, 'stderr': stderr, 'code': exit_code})
