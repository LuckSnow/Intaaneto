"""Cloudflare R2 storage backends used only when explicitly enabled."""

from pathlib import PurePosixPath
from uuid import uuid4

from django.core.exceptions import SuspiciousFileOperation
from storages.backends.s3 import S3Storage


class PrivateR2Storage(S3Storage):
    """Private S3-compatible storage with application-owned object names."""

    def get_available_name(self, name, max_length=None):
        original = PurePosixPath(name)
        suffix = original.suffix.lower()[:16]
        generated = str(original.parent / f"{uuid4().hex}{suffix}")
        if max_length and len(generated) > max_length:
            raise SuspiciousFileOperation(
                "Generated private media object name exceeds its field limit."
            )
        # UUID names do not need an existence probe. Avoiding HEAD here also
        # keeps a credential or network failure from occurring before _save.
        return generated
