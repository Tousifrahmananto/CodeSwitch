from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0003_codefile_user_updated_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='codefile',
            name='language',
            field=models.CharField(
                choices=[
                    ('python', 'Python'),
                    ('c', 'C'),
                    ('java', 'Java'),
                    ('javascript', 'JavaScript'),
                    ('cpp', 'C++'),
                    ('other', 'Other'),
                ],
                default='other',
                max_length=20,
            ),
        ),
    ]
