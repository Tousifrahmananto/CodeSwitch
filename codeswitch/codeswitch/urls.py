from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .admin_views import (
    AdminStatsView, AdminUsersView, AdminUserDetailView,
    AdminConversionsView, AdminModulesView, AdminModuleDetailView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('converter.urls')),
    path('api/', include('files.urls')),
    path('api/', include('learning.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Admin API
    path('api/admin/stats',            AdminStatsView.as_view()),
    path('api/admin/users',            AdminUsersView.as_view()),
    path('api/admin/users/<int:pk>',   AdminUserDetailView.as_view()),
    path('api/admin/conversions',      AdminConversionsView.as_view()),
    path('api/admin/modules',          AdminModulesView.as_view()),
    path('api/admin/modules/<int:pk>', AdminModuleDetailView.as_view()),
]
