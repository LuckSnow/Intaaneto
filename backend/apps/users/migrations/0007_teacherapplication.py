from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_verification_token_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specialization', models.CharField(max_length=255)),
                ('years_of_experience', models.PositiveSmallIntegerField(default=0)),
                ('reason', models.TextField(max_length=2000)),
                ('status', models.CharField(choices=[('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'), ('rejected', 'Từ chối')], default='pending', max_length=20)),
                ('review_note', models.TextField(blank=True, max_length=1000)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_applications', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_teacher_applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-submitted_at'],
                'indexes': [models.Index(fields=['status', '-submitted_at'], name='users_teach_status_6b478c_idx')],
                'constraints': [models.UniqueConstraint(condition=models.Q(('status', 'pending')), fields=('applicant',), name='unique_pending_teacher_application')],
            },
        ),
    ]
