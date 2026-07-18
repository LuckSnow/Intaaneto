from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_google_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='verification_token_created_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='verification token created at',
            ),
        ),
    ]
