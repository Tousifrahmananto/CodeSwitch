from django.urls import path
from .views import ConvertCodeView, ConversionHistoryView, CreateSnippetView, GetSnippetView

urlpatterns = [
    path('convert', ConvertCodeView.as_view(), name='convert'),
    path('convert/history', ConversionHistoryView.as_view(), name='conversion-history'),
    path('snippets/', CreateSnippetView.as_view(), name='create-snippet'),
    path('snippets/<uuid:slug>/', GetSnippetView.as_view(), name='get-snippet'),
]
