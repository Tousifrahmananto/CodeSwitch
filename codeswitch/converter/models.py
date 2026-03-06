from django.db import models
from django.conf import settings

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('c', 'C'),
    ('java', 'Java'),
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
