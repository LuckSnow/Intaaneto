from urllib.parse import parse_qs, urlparse

from .storage import PrivateR2Storage


def make_storage():
    return PrivateR2Storage(
        access_key="test-access-key",
        secret_key="test-secret-key",
        bucket_name="private-bucket",
        endpoint_url="https://account-id.r2.cloudflarestorage.com",
        region_name="auto",
        signature_version="s3v4",
        querystring_auth=True,
        querystring_expire=300,
        location="test/private-media",
        file_overwrite=False,
    )


def test_r2_object_name_is_server_generated_and_keeps_safe_scope():
    storage = make_storage()

    generated = storage.get_available_name("courses/uploads/teacher-name.PDF")

    assert generated.startswith("courses/uploads/")
    assert generated.endswith(".pdf")
    assert "teacher-name" not in generated
    assert len(generated.removeprefix("courses/uploads/").removesuffix(".pdf")) == 32


def test_private_r2_url_is_signed_and_short_lived():
    storage = make_storage()

    url = storage.url("courses/videos/lesson.mp4")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "account-id.r2.cloudflarestorage.com"
    assert parsed.path == "/private-bucket/test/private-media/courses/videos/lesson.mp4"
    assert query["X-Amz-Expires"] == ["300"]
    assert "X-Amz-Signature" in query
    assert "test-secret-key" not in url
