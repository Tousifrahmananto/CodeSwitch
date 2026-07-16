from django.db import migrations, models
from django.db.models import Count, Q
from django.db.models.functions import Lower


def prepare_verified_emails(apps, schema_editor):
    User = apps.get_model('users', 'User')
    duplicates = list(
        User.objects.exclude(email='')
        .annotate(normalized_email=Lower('email'))
        .values('normalized_email')
        .annotate(total=Count('id'))
        .filter(total__gt=1)
        .values_list('normalized_email', flat=True)
    )
    if duplicates:
        raise RuntimeError(
            'Duplicate case-insensitive user emails must be resolved before migration: '
            + ', '.join(duplicates[:10])
        )
    User.objects.filter(google_email_verified=True).update(email_verified=True)


class Migration(migrations.Migration):
    dependencies = [('users', '0004_user_avatar_blob_user_avatar_content_type_and_more')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(prepare_verified_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(
                Lower('email'),
                condition=~Q(email=''),
                name='users_user_email_ci_unique',
            ),
        ),
    ]
