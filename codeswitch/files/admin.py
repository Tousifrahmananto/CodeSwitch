from django.contrib import admin
from .models import CodeFile


@admin.register(CodeFile)
class CodeFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'user', 'language', 'created_at', 'updated_at')
    list_filter = ('language',)
    search_fields = ('filename', 'user__username')
    ordering = ('-updated_at',)
