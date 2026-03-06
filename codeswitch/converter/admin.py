from django.contrib import admin
from .models import ConversionHistory


@admin.register(ConversionHistory)
class ConversionHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_language', 'target_language', 'timestamp')
    list_filter = ('source_language', 'target_language')
    search_fields = ('user__username',)
    ordering = ('-timestamp',)
