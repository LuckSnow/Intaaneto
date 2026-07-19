import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_lessonmultimediajob'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonVideoScriptDraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=4800)),
                ('status', models.CharField(choices=[('draft', 'Bản nháp'), ('approved', 'Đã duyệt')], default='draft', max_length=20)),
                ('source_checksum', models.CharField(max_length=64)),
                ('source_version', models.PositiveIntegerField()),
                ('summary_checksum', models.CharField(max_length=64)),
                ('provider', models.CharField(max_length=32)),
                ('model', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_lesson_video_scripts', to=settings.AUTH_USER_MODEL)),
                ('generated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_lesson_video_script_drafts', to=settings.AUTH_USER_MODEL)),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='video_script_draft', to='courses.lesson')),
            ],
        ),
        migrations.AlterField(
            model_name='lessonmultimediajob',
            name='approved_script',
            field=models.TextField(max_length=4800),
        ),
    ]
