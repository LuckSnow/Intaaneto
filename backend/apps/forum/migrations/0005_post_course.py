from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0009_lessonvideoscriptdraft_and_job_script_length'),
        ('forum', '0004_reaction_reaction_has_exactly_one_target_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='course',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='forum_posts',
                to='courses.course',
            ),
        ),
    ]
