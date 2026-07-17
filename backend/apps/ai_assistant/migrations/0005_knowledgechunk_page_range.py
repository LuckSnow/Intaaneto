import re

from django.db import migrations, models
from django.db.models import F, Q


PAGE_MARKER = re.compile(r'^--- Trang ([1-9]\d*) ---$', re.MULTILINE)


def backfill_pdf_page_ranges(apps, schema_editor):
    KnowledgeSource = apps.get_model('ai_assistant', 'KnowledgeSource')
    for source in KnowledgeSource.objects.filter(source_type='extracted_text').iterator():
        text = source.normalized_text
        markers = [
            (match.start(), int(match.group(1)))
            for match in PAGE_MARKER.finditer(text)
        ]
        if not markers:
            continue
        intervals = [
            (
                offset,
                markers[index + 1][0] if index + 1 < len(markers) else len(text),
                page,
            )
            for index, (offset, page) in enumerate(markers)
        ]
        for chunk in source.chunks.all().iterator():
            pages = [
                page
                for start, end, page in intervals
                if start < chunk.end_offset and end > chunk.start_offset
            ]
            if pages:
                chunk.page_start = pages[0]
                chunk.page_end = pages[-1]
                chunk.save(update_fields=['page_start', 'page_end'])


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0004_chatmessage_retrieval_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='knowledgechunk',
            name='page_start',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='knowledgechunk',
            name='page_end',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_pdf_page_ranges, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='knowledgechunk',
            constraint=models.CheckConstraint(
                check=(
                    Q(page_start__isnull=True, page_end__isnull=True)
                    | Q(
                        page_start__isnull=False,
                        page_end__isnull=False,
                        page_end__gte=F('page_start'),
                    )
                ),
                name='knowledge_chunk_valid_page_range',
            ),
        ),
    ]
