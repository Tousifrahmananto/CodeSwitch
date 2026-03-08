from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import CookieTokenRefreshView
from .admin_views import (
    AdminStatsView, AdminUsersView, AdminUserDetailView,
    AdminConversionsView, AdminModulesView, AdminModuleDetailView,
    AdminModuleLessonsView, AdminLessonDetailView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('converter.urls')),
    path('api/', include('files.urls')),
    path('api/', include('learning.urls')),
    # Cookie-based token refresh — reads refresh_token cookie, sets new cookies
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),

    # Admin API
    path('api/admin/stats',                             AdminStatsView.as_view()),
    path('api/admin/users',                             AdminUsersView.as_view()),
    path('api/admin/users/<int:pk>',                    AdminUserDetailView.as_view()),
    path('api/admin/conversions',                       AdminConversionsView.as_view()),
    path('api/admin/modules',                           AdminModulesView.as_view()),
    path('api/admin/modules/<int:pk>',                  AdminModuleDetailView.as_view()),
    path('api/admin/modules/<int:pk>/lessons',          AdminModuleLessonsView.as_view()),
    path('api/admin/lessons/<int:pk>',                  AdminLessonDetailView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
