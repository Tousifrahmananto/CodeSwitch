from django.db import models
from django.conf import settings

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('c', 'C'),
    ('java', 'Java'),
    ('javascript', 'JavaScript'),
    ('other', 'Other'),
]


class CodeFile(models.Model):
    """A code file saved by a user in their workspace."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='code_files'
    )
    filename = models.CharField(max_length=255)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='other')
    code_content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}/{self.filename}"
