from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.utils import timezone
from .models import LearningModule, Lesson, UserProgress


# ── Serializers ──────────────────────────────

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'content', 'example_code', 'order')


class ModuleSerializer(serializers.ModelSerializer):
    lesson_count = serializers.SerializerMethodField()

    class Meta:
        model = LearningModule
        fields = ('id', 'title', 'description', 'difficulty', 'language', 'lesson_count')

    def get_lesson_count(self, obj):
        return obj.lessons.count()


class ModuleDetailSerializer(ModuleSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ('lessons',)


class ProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True)

    class Meta:
        model = UserProgress
        fields = ('id', 'lesson_id', 'module_title', 'lesson_title', 'completed', 'completion_date')


# ── Views ─────────────────────────────────────

class ModuleListView(generics.ListAPIView):
    """GET /api/modules — List all available learning modules."""
    queryset = LearningModule.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]


class ModuleDetailView(generics.RetrieveAPIView):
    """GET /api/modules/{id} — Get a module with its lessons."""
    queryset = LearningModule.objects.all()
    serializer_class = ModuleDetailSerializer
    permission_classes = [IsAuthenticated]


class ModuleLessonsView(generics.ListAPIView):
    """GET /api/modules/{id}/lessons — Get just the lessons for a module."""
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(module_id=self.kwargs['pk'])


class UpdateProgressView(APIView):
    """POST /api/progress/update — Mark a lesson as complete."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lesson_id = request.data.get('lesson_id')
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        progress, _ = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={'module': lesson.module}
        )
        progress.completed = True
        progress.completion_date = timezone.now()
        progress.save()
        return Response({'message': f'Lesson "{lesson.title}" marked as complete.'})


class GetProgressView(generics.ListAPIView):
    """GET /api/progress — Get the current user's learning progress."""
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)
