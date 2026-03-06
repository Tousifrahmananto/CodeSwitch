from django.urls import path
from .views import ModuleListView, ModuleDetailView, ModuleLessonsView, UpdateProgressView, GetProgressView

urlpatterns = [
    path('modules', ModuleListView.as_view(), name='module-list'),
    path('modules/<int:pk>', ModuleDetailView.as_view(), name='module-detail'),
    path('modules/<int:pk>/lessons', ModuleLessonsView.as_view(), name='module-lessons'),
    path('progress/update', UpdateProgressView.as_view(), name='progress-update'),
    path('progress', GetProgressView.as_view(), name='progress-list'),
]
