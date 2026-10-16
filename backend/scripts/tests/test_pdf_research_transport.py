import json
from pathlib import Path
from types import SimpleNamespace
import tarfile

from scripts.pdf_research import upload


def test_upload_streams_only_pdf_members(tmp_path):
    folder = tmp_path / 'pdfs'
    folder.mkdir()
    (folder / 'lecture.pdf').write_bytes(b'%PDF-test')
    (folder / '.env').write_text('secret must not be transferred')
    received = []

    class FakeDocker:
        def execute(self, argv, **kwargs):
            if 'stdin' in kwargs:
                with tarfile.open(fileobj=kwargs['stdin'], mode='r') as archive:
                    received.extend((m.name, archive.extractfile(m).read()) for m in archive)

        def fetch(self, remote, local):
            Path(local).write_text(json.dumps({'mode': 'dry_run', 'files': []}))

    args = SimpleNamespace(pdf_dir=folder, actor_id=1, course_id=1, execute=False, wait=False)
    upload(args, FakeDocker(), tmp_path / 'manifest.json')
    assert received == [('lecture.pdf', b'%PDF-test')]
