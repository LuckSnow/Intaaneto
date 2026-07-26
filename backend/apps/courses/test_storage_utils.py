from io import BytesIO
from pathlib import Path

import pytest

from .storage_utils import StoredFileTooLarge, local_path_for_stored_file


class RemoteFieldFile:
    def __init__(self, content):
        self._content = content
        self._stream = None
        self.name = "private/input.bin"
        self.opened = False

    @property
    def size(self):
        return len(self._content)

    @property
    def path(self):
        raise NotImplementedError

    def open(self, mode):
        assert mode == "rb"
        self.opened = True
        self._stream = BytesIO(self._content)

    def chunks(self, chunk_size=3):
        while chunk := self._stream.read(chunk_size):
            yield chunk

    def close(self):
        self._stream.close()

    def __bool__(self):
        return True


def test_remote_stored_file_is_materialized_and_cleaned_up():
    field_file = RemoteFieldFile(b"private media")

    with local_path_for_stored_file(
        field_file,
        max_bytes=100,
        suffix=".bin",
    ) as local_path:
        assert local_path.read_bytes() == b"private media"
        assert local_path.suffix == ".bin"
        materialized_path = local_path

    assert field_file.opened is True
    assert not materialized_path.exists()


def test_oversized_remote_stored_file_is_rejected_before_download():
    field_file = RemoteFieldFile(b"too large")

    with pytest.raises(StoredFileTooLarge):
        with local_path_for_stored_file(field_file, max_bytes=2):
            pass

    assert field_file.opened is False


def test_filesystem_stored_file_reuses_existing_path(tmp_path):
    local_file = tmp_path / "input.wav"
    local_file.write_bytes(b"audio")

    class LocalFieldFile:
        size = 5
        path = str(local_file)

        def __bool__(self):
            return True

    with local_path_for_stored_file(LocalFieldFile(), max_bytes=10) as local_path:
        assert local_path == Path(local_file)

    assert local_file.exists()
