from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('converter', '0003_sharedsnippet_and_more')]
    operations = [
        migrations.AddIndex(
            model_name='conversionhistory',
            index=models.Index(fields=['user', '-timestamp'], name='conv_user_time_idx'),
        ),
    ]
