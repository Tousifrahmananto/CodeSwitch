from django.urls import path
from .views import ConvertCodeView, ConversionHistoryView, CreateSnippetView, GetSnippetView, RunCodeView, ExplainCodeView

urlpatterns = [
    path('convert', ConvertCodeView.as_view(), name='convert'),
    path('convert/history', ConversionHistoryView.as_view(), name='conversion-history'),
    path('snippets/', CreateSnippetView.as_view(), name='create-snippet'),
    path('snippets/<uuid:slug>/', GetSnippetView.as_view(), name='get-snippet'),
    path('run/', RunCodeView.as_view(), name='run-code'),
    path('explain/', ExplainCodeView.as_view(), name='explain-code'),
]
