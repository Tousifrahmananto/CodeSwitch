from django.urls import path
from .views import ConvertCodeView, ConversionHistoryView

urlpatterns = [
    path('convert', ConvertCodeView.as_view(), name='convert'),
    path('convert/history', ConversionHistoryView.as_view(), name='conversion-history'),
]
