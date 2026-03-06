from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from .models import CodeFile


class CodeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeFile
        fields = ('id', 'filename', 'language', 'code_content', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class FileListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/files — List all files for the current user.
    POST /api/files — Create a new file.
    """
    serializer_class = CodeFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CodeFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/files/{id} — Retrieve a specific file.
    PUT    /api/files/{id} — Update a file.
    DELETE /api/files/{id} — Delete a file.
    """
    serializer_class = CodeFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only access their own files
        return CodeFile.objects.filter(user=self.request.user)
