import uuid
from django.db import models
from django.conf import settings

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('c', 'C'),
    ('java', 'Java'),
    ('javascript', 'JavaScript'),
    ('cpp', 'C++'),
]


class ConversionHistory(models.Model):
    """Stores every code conversion a user performs."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversions'
    )
    source_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    target_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    input_code = models.TextField()
    output_code = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.source_language} → {self.target_language} ({self.timestamp})"


class SharedSnippet(models.Model):
    """A publicly-shareable read-only snapshot of a conversion."""
    slug = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)
    source_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    target_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    input_code = models.TextField()
    output_code = models.TextField()
    engine = models.CharField(max_length=10, default='ai')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Snippet {self.slug} ({self.source_language}→{self.target_language})"
