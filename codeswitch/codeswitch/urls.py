from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as serve_media
from users.views import CookieTokenRefreshView
from .admin_views import (
    AdminStatsView, AdminUsersView, AdminUserDetailView,
    AdminConversionsView, AdminModulesView, AdminModuleDetailView,
    AdminModuleLessonsView, AdminLessonDetailView,
)
from .system_views import live, ready, metrics

urlpatterns = [
    path('health/live', live, name='health-live'),
    path('health/ready', ready, name='health-ready'),
    path('metrics', metrics, name='metrics'),
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
]

# Legacy file-backed avatars are available only in local development. Production
# avatars are served from the database representation, not Django's static helper.
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
    ]
