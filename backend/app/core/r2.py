"""Cloudflare R2 client wrapper (S3-compatible) — Phase 2.2.5.

R2 exposes an S3 API at ``https://<account-id>.r2.cloudflarestorage.com``.
We use boto3 with ``signature_version='s3v4'`` and force path-style addressing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PresignedPutSpec:
    """Result of presigning a PUT URL."""

    url: str
    fields: dict[str, str]
    expires_in: int


def _endpoint_url(account_id: str) -> str:
    return f"https://{account_id}.r2.cloudflarestorage.com"


def _client(settings):
    """Build a boto3 S3 client pointed at R2. Importing boto3 lazily keeps
    test environments without R2 creds happy."""
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=_endpoint_url(settings.r2_account_id),
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def presign_put(
    settings, *, key: str, content_type: str, expires_in: int | None = None
) -> PresignedPutSpec:
    """Presign a PUT URL for the given key. Uses ``boto3.generate_presigned_url``."""
    expiry = expires_in or settings.photo_upload_ttl_seconds
    client = _client(settings)
    url = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.r2_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expiry,
    )
    # The browser must send Content-Type matching the signature
    return PresignedPutSpec(url=url, fields={"Content-Type": content_type}, expires_in=expiry)


def head_object(settings, key: str) -> dict | None:
    """Return the HEAD metadata of an object, or None if missing."""
    import botocore.exceptions

    client = _client(settings)
    try:
        return client.head_object(Bucket=settings.r2_bucket, Key=key)
    except botocore.exceptions.ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def get_object_prefix(settings, key: str, *, n_bytes: int = 16) -> bytes | None:
    """Return the first ``n_bytes`` of an object via Range GET.

    Used by the photo-claim path to magic-byte-sniff uploaded bytes
    independently of the client-claimed Content-Type. Returns ``None`` if
    the object is missing.
    """
    import botocore.exceptions

    client = _client(settings)
    try:
        resp = client.get_object(
            Bucket=settings.r2_bucket,
            Key=key,
            Range=f"bytes=0-{max(0, n_bytes - 1)}",
        )
    except botocore.exceptions.ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchKey", "NotFound"):
            return None
        raise
    body = resp.get("Body")
    if body is None:
        return b""
    return body.read()


def copy_object(settings, *, src_key: str, dest_key: str) -> None:
    client = _client(settings)
    client.copy_object(
        Bucket=settings.r2_bucket,
        CopySource={"Bucket": settings.r2_bucket, "Key": src_key},
        Key=dest_key,
    )


def delete_object(settings, key: str) -> None:
    client = _client(settings)
    client.delete_object(Bucket=settings.r2_bucket, Key=key)


def public_url_for(settings, key: str) -> str:
    base = settings.r2_public_base_url.rstrip("/")
    if not base:
        return f"r2://{settings.r2_bucket}/{key}"
    return f"{base}/{key}"


# Magic-byte image sniff (used by the claim path to confirm bytes are
# actually an image). Pure-Python so no dependency on PIL.
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
WEBP_MAGIC = b"RIFF"  # followed by 4 size bytes and "WEBP"


def looks_like_image(prefix_bytes: bytes) -> bool:
    if prefix_bytes.startswith(JPEG_MAGIC):
        return True
    if prefix_bytes.startswith(PNG_MAGIC):
        return True
    if prefix_bytes.startswith(WEBP_MAGIC) and b"WEBP" in prefix_bytes[:16]:
        return True
    return False
