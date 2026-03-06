from django.contrib import admin
from .models import LearningModule, Lesson, UserProgress


@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'difficulty')
    list_filter = ('language', 'difficulty')
    search_fields = ('title',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module',)
    ordering = ('module', 'order')


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'lesson', 'completed', 'completion_date')
    list_filter = ('completed',)
    search_fields = ('user__username',)
