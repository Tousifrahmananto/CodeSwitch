from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import serializers
from .services import convert_code
from .models import ConversionHistory, SharedSnippet


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
