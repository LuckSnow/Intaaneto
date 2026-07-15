from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0003_knowledgesource_knowledgechunk_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='retrieval_metadata',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
