from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0003_assessmentreinforcementevent_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DialogueKnowledgeCheckEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assessment_version', models.PositiveIntegerField()),
                ('learning_objective_snapshot', models.CharField(max_length=255)),
                ('outcome', models.CharField(choices=[('demonstrated', 'Demonstrated'), ('partial', 'Partial'), ('not_demonstrated', 'Not demonstrated'), ('unavailable', 'Unavailable')], max_length=24)),
                ('answer_digest', models.CharField(max_length=64)),
                ('evidence_chunk_ids', models.JSONField(blank=True, default=list)),
                ('generation_provider', models.CharField(blank=True, max_length=32)),
                ('generation_model', models.CharField(blank=True, max_length=100)),
                ('tokens_used', models.PositiveIntegerField(blank=True, null=True)),
                ('latency_ms', models.PositiveIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='dialogue_check_events', to='exercises.assessmentattempt')),
                ('question', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dialogue_check_events', to='exercises.assessmentquestion')),
            ],
            options={
                'ordering': ['-created_at', '-id'],
                'indexes': [models.Index(fields=['attempt', '-created_at'], name='exercises_d_attempt_1893c5_idx'), models.Index(fields=['outcome', '-created_at'], name='exercises_d_outcome_8b4cb7_idx')],
            },
        ),
    ]
