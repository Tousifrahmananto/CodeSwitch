from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('users', '0002_alter_user_avatar')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='google_sub',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='google_email_verified',
            field=models.BooleanField(default=False),
        ),
    ]
