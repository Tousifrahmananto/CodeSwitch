from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('files', '0002_initial')]
    operations = [
        migrations.AddIndex(
            model_name='codefile',
            index=models.Index(fields=['user', '-updated_at'], name='file_user_time_idx'),
        ),
    ]
