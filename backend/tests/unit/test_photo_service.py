"""Unit tests for photo upload helpers (Phase 2.2.5)."""

from __future__ import annotations

import uuid

from app.core.r2 import looks_like_image
from app.services.photo_service import (
    ALLOWED_CONTENT_TYPES,
    canonical_object_key,
    temp_object_key,
)


def test_temp_key_uses_tmp_prefix():
    uid = uuid.uuid4()
    k = temp_object_key(uid, "image/jpeg")
    assert k.startswith("tmp/")
    assert str(uid) in k
    assert k.endswith(".jpg")


def test_temp_key_extension_per_content_type():
    uid = uuid.uuid4()
    assert temp_object_key(uid, "image/png").endswith(".png")
    assert temp_object_key(uid, "image/webp").endswith(".webp")


def test_canonical_key_uses_photos_prefix():
    uid = uuid.uuid4()
    k = canonical_object_key(uid, "image/jpeg")
    assert k.startswith("photos/")
    assert k.endswith(".jpg")


def test_allowed_content_types_set():
    assert ALLOWED_CONTENT_TYPES == {"image/jpeg", "image/png", "image/webp"}


def test_looks_like_image_jpeg():
    assert looks_like_image(b"\xff\xd8\xff\xe0\x00\x10JFIF") is True


def test_looks_like_image_png():
    assert looks_like_image(b"\x89PNG\r\n\x1a\nIHDR") is True


def test_looks_like_image_webp():
    # RIFF<size>WEBP
    assert looks_like_image(b"RIFF\x00\x00\x00\x00WEBPVP8 ") is True


def test_looks_like_image_rejects_text():
    assert looks_like_image(b"not an image") is False
