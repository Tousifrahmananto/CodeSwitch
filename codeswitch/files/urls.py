from django.urls import path
from .views import FileListCreateView, FileDetailView

urlpatterns = [
    path('files', FileListCreateView.as_view(), name='file-list'),
    path('files/<int:pk>', FileDetailView.as_view(), name='file-detail'),
]
