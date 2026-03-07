from django.urls import path
from .views import (
    ModuleListView, ModuleDetailView, ModuleLessonsView,
    UpdateProgressView, GetProgressView,
    GetLessonQuizView, SubmitQuizAttemptView,
)

urlpatterns = [
    path('modules', ModuleListView.as_view(), name='module-list'),
    path('modules/<int:pk>', ModuleDetailView.as_view(), name='module-detail'),
    path('modules/<int:pk>/lessons', ModuleLessonsView.as_view(), name='module-lessons'),
    path('progress/update', UpdateProgressView.as_view(), name='progress-update'),
    path('progress', GetProgressView.as_view(), name='progress-list'),
    path('lessons/<int:lesson_id>/quiz/', GetLessonQuizView.as_view(), name='lesson-quiz'),
    path('quizzes/<int:quiz_id>/submit/', SubmitQuizAttemptView.as_view(), name='quiz-submit'),
]
