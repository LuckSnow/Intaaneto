"""Helpers for consumers that require a local path from remote-backed media."""

from contextlib import contextmanager
from pathlib import Path
import tempfile


class StoredFileTooLarge(ValueError):
    """Raised before copying an unexpectedly large stored object locally."""


def _filesystem_path(field_file):
    try:
        return field_file.path
    except (AttributeError, NotImplementedError):
        return None


@contextmanager
def local_path_for_stored_file(field_file, *, max_bytes, suffix=""):
    """Yield a local path for a FileField without assuming storage has ``path``.

    Filesystem storage returns its existing path. Remote storage is streamed to
    a bounded temporary file and removed when the caller leaves the context.
    """

    if not field_file:
        raise ValueError("A stored file is required.")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive.")

    size = field_file.size
    if size > max_bytes:
        raise StoredFileTooLarge("Stored file exceeds the local processing limit.")

    local_path = _filesystem_path(field_file)
    if local_path:
        yield Path(local_path)
        return

    temporary = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    temporary_path = Path(temporary.name)
    copied = 0
    try:
        field_file.open("rb")
        try:
            for chunk in field_file.chunks():
                copied += len(chunk)
                if copied > max_bytes:
                    raise StoredFileTooLarge(
                        "Stored file exceeds the local processing limit."
                    )
                temporary.write(chunk)
        finally:
            field_file.close()
        temporary.close()
        yield temporary_path
    finally:
        if not temporary.closed:
            temporary.close()
        temporary_path.unlink(missing_ok=True)
