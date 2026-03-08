"""
Admin API Views — staff-only endpoints for the React admin dashboard.
All views require the requesting user to be authenticated AND is_staff=True.
"""
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from converter.models import ConversionHistory
from files.models import CodeFile
from learning.models import LearningModule, Lesson

User = get_user_model()


class IsStaffUser(BasePermission):
    """Allows access only to staff (admin) users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


# ── Stats ─────────────────────────────────────────────────────────────────────

class AdminStatsView(APIView):
    """GET /api/admin/stats — overview counters for the dashboard."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        week_ago = timezone.now() - timedelta(days=7)
        return Response({
            'total_users':            User.objects.count(),
            'total_conversions':      ConversionHistory.objects.count(),
            'total_files':            CodeFile.objects.count(),
            'total_modules':          LearningModule.objects.count(),
            'conversions_this_week':  ConversionHistory.objects.filter(timestamp__gte=week_ago).count(),
            'new_users_this_week':    User.objects.filter(date_joined__gte=week_ago).count(),
        })


# ── Users ─────────────────────────────────────────────────────────────────────

class AdminUsersView(APIView):
    """GET /api/admin/users — list all users."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 100)), 500)
        users = (
            User.objects
            .annotate(conversion_count=Count('conversions'))
            .order_by('-date_joined')
            .values('id', 'username', 'email', 'is_staff', 'is_active',
                    'date_joined', 'conversion_count')
        )[:limit]
        return Response(list(users))


class AdminUserDetailView(APIView):
    """PATCH /api/admin/users/:id — toggle staff/active. DELETE — remove user."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def _get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Safety: can't remove your own staff status
        if user == request.user and request.data.get('is_staff') is False:
            return Response({'error': 'Cannot remove your own staff status.'}, status=status.HTTP_400_BAD_REQUEST)

        if 'is_staff' in request.data:
            user.is_staff = bool(request.data['is_staff'])
        if 'is_active' in request.data:
            user.is_active = bool(request.data['is_active'])
        user.save(update_fields=['is_staff', 'is_active'])

        return Response({
            'id': user.id,
            'username': user.username,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
        })

    def delete(self, request, pk):
        user = self._get_user(pk)
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user == request.user:
            return Response({'error': 'Cannot delete your own account.'}, status=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Conversions ───────────────────────────────────────────────────────────────

class AdminConversionsView(APIView):
    """GET /api/admin/conversions — latest 100 conversions across all users."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        qs = (
            ConversionHistory.objects
            .select_related('user')
            .order_by('-timestamp')[:100]
        )
        return Response([
            {
                'id':              c.id,
                'user':            c.user.username,
                'source_language': c.source_language,
                'target_language': c.target_language,
                'timestamp':       c.timestamp,
            }
            for c in qs
        ])


# ── Learning Modules ──────────────────────────────────────────────────────────

class AdminModulesView(APIView):
    """GET /api/admin/modules — list. POST — create."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        modules = (
            LearningModule.objects
            .annotate(lesson_count=Count('lessons'))
            .order_by('id')
            .values('id', 'title', 'description', 'language', 'difficulty', 'lesson_count')
        )
        return Response(list(modules))

    def post(self, request):
        title = request.data.get('title', '').strip()
        if not title:
            return Response({'error': 'Title is required.'}, status=status.HTTP_400_BAD_REQUEST)

        module = LearningModule.objects.create(
            title=title,
            description=request.data.get('description', ''),
            language=request.data.get('language', 'general'),
            difficulty=request.data.get('difficulty', 'beginner'),
        )
        return Response({'id': module.id, 'title': module.title}, status=status.HTTP_201_CREATED)


class AdminModuleDetailView(APIView):
    """PUT /api/admin/modules/:id — update. DELETE — remove."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def _get_module(self, pk):
        try:
            return LearningModule.objects.get(pk=pk)
        except LearningModule.DoesNotExist:
            return None

    def put(self, request, pk):
        module = self._get_module(pk)
        if not module:
            return Response({'error': 'Module not found.'}, status=status.HTTP_404_NOT_FOUND)

        module.title       = request.data.get('title', module.title)
        module.description = request.data.get('description', module.description)
        module.language    = request.data.get('language', module.language)
        module.difficulty  = request.data.get('difficulty', module.difficulty)
        module.save()
        return Response({'id': module.id, 'title': module.title})

    def delete(self, request, pk):
        module = self._get_module(pk)
        if not module:
            return Response({'error': 'Module not found.'}, status=status.HTTP_404_NOT_FOUND)
        module.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Learning Lessons ───────────────────────────────────────────────────────────

class AdminModuleLessonsView(APIView):
    """GET /api/admin/modules/:pk/lessons — list lessons. POST — create."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def _get_module(self, pk):
        try:
            return LearningModule.objects.get(pk=pk)
        except LearningModule.DoesNotExist:
            return None

    def get(self, request, pk):
        module = self._get_module(pk)
        if not module:
            return Response({'error': 'Module not found.'}, status=status.HTTP_404_NOT_FOUND)
        lessons = module.lessons.order_by('order').select_related('quiz')
        result = []
        for lesson in lessons:
            try:
                has_quiz = lesson.quiz is not None
            except Exception:
                has_quiz = False
            result.append({
                'id':       lesson.id,
                'title':    lesson.title,
                'order':    lesson.order,
                'has_quiz': has_quiz,
            })
        return Response(result)

    def post(self, request, pk):
        module = self._get_module(pk)
        if not module:
            return Response({'error': 'Module not found.'}, status=status.HTTP_404_NOT_FOUND)

        title = request.data.get('title', '').strip()
        if not title:
            return Response({'error': 'Title is required.'}, status=status.HTTP_400_BAD_REQUEST)

        lesson = Lesson.objects.create(
            module=module,
            title=title,
            content=request.data.get('content', ''),
            example_code=request.data.get('example_code', '{}'),
            order=request.data.get('order', module.lessons.count() + 1),
        )
        return Response({'id': lesson.id, 'title': lesson.title}, status=status.HTTP_201_CREATED)


class AdminLessonDetailView(APIView):
    """GET /api/admin/lessons/:pk — get lesson. PUT — update. DELETE — remove."""
    permission_classes = [IsAuthenticated, IsStaffUser]

    def _get_lesson(self, pk):
        try:
            return Lesson.objects.get(pk=pk)
        except Lesson.DoesNotExist:
            return None

    def get(self, request, pk):
        lesson = self._get_lesson(pk)
        if not lesson:
            return Response({'error': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            'id':           lesson.id,
            'title':        lesson.title,
            'content':      lesson.content,
            'example_code': lesson.example_code,
            'order':        lesson.order,
        })

    def put(self, request, pk):
        lesson = self._get_lesson(pk)
        if not lesson:
            return Response({'error': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        lesson.title        = request.data.get('title', lesson.title)
        lesson.content      = request.data.get('content', lesson.content)
        lesson.example_code = request.data.get('example_code', lesson.example_code)
        lesson.order        = request.data.get('order', lesson.order)
        lesson.save()
        return Response({'id': lesson.id, 'title': lesson.title})

    def delete(self, request, pk):
        lesson = self._get_lesson(pk)
        if not lesson:
            return Response({'error': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
