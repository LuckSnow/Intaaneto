import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0005_knowledgechunk_page_range'),
        ('courses', '0005_lessonvideogenerationjob'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonIngestionJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('queued', 'Chờ chạy'), ('running', 'Đang chạy'), ('completed', 'Hoàn thành'), ('failed', 'Thất bại')], default='queued', max_length=20)),
                ('task_id', models.UUIDField(unique=True)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('index_created', models.BooleanField(blank=True, null=True)),
                ('failure_code', models.CharField(blank=True, max_length=50)),
                ('safe_error', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('knowledge_source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ingestion_jobs', to='ai_assistant.knowledgesource')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingestion_jobs', to='courses.lesson')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requested_lesson_ingestion_jobs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at', '-id'],
                'indexes': [models.Index(fields=['lesson', '-created_at'], name='courses_les_lesson__76d3f2_idx'), models.Index(fields=['status', '-created_at'], name='courses_les_status_4986fc_idx')],
                'constraints': [models.UniqueConstraint(condition=models.Q(('status__in', ('queued', 'running'))), fields=('lesson',), name='unique_active_ingestion_job_per_lesson')],
            },
        ),
    ]
