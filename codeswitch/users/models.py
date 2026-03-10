from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


def _validate_avatar(file):
    """Validate avatar file type and size."""
    # Check file size (max 5 MB)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Avatar file must be under 5 MB.")

    # Only allow image types that are safe
    allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
    if hasattr(file, 'content_type') and file.content_type not in allowed_types:
        raise ValidationError("Avatar must be JPEG, PNG, or WebP. SVG and other formats not allowed.")


class User(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        validators=[_validate_avatar],
        help_text="Max 5 MB. Allowed: JPEG, PNG, WebP only."
    )

    def __str__(self):
        return self.username
