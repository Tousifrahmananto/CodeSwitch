from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_google_auth'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar_blob',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='avatar_content_type',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='avatar_filename',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
