from django.db import migrations, models

import users.models


class Migration(migrations.Migration):
    dependencies = [('users', '0001_initial')]
    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(
                blank=True,
                help_text='Max 5 MB. Allowed: JPEG, PNG, WebP only.',
                null=True,
                upload_to='avatars/',
                validators=[users.models._validate_avatar],
            ),
        ),
    ]
