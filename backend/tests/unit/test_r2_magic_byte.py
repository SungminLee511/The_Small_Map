"""Unit tests for r2.get_object_prefix + magic-byte helpers — Phase 5.4."""

from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import botocore.exceptions

from app.core import r2


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        r2_account_id="acc",
        r2_access_key_id="ak",
        r2_secret_access_key="sk",
        r2_bucket="b",
    )


def test_looks_like_image_for_known_magic():
    assert r2.looks_like_image(b"\xff\xd8\xff\xe0junk")  # JPEG
    assert r2.looks_like_image(b"\x89PNG\r\n\x1a\nrest")  # PNG
    assert r2.looks_like_image(b"RIFF\x00\x00\x00\x00WEBPxx")  # WebP


def test_looks_like_image_rejects_garbage():
    assert not r2.looks_like_image(b"<html><body>")
    assert not r2.looks_like_image(b"")
    assert not r2.looks_like_image(b"RIFF\x00\x00\x00\x00WAVE")  # not webp


def test_get_object_prefix_returns_bytes(monkeypatch):
    fake_client = MagicMock()
    fake_client.get_object.return_value = {"Body": BytesIO(b"\xff\xd8\xff\xe0abcd")}
    monkeypatch.setattr(r2, "_client", lambda _s: fake_client)

    out = r2.get_object_prefix(_settings(), "tmp/x.jpg", n_bytes=8)
    assert out == b"\xff\xd8\xff\xe0abcd"
    fake_client.get_object.assert_called_once()
    kwargs = fake_client.get_object.call_args.kwargs
    assert kwargs["Range"] == "bytes=0-7"


def test_get_object_prefix_returns_none_when_missing(monkeypatch):
    fake_client = MagicMock()
    fake_client.get_object.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "NoSuchKey"}}, "GetObject"
    )
    monkeypatch.setattr(r2, "_client", lambda _s: fake_client)

    assert r2.get_object_prefix(_settings(), "tmp/missing.jpg") is None


def test_get_object_prefix_propagates_unknown_errors(monkeypatch):
    fake_client = MagicMock()
    fake_client.get_object.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDenied"}}, "GetObject"
    )
    monkeypatch.setattr(r2, "_client", lambda _s: fake_client)

    try:
        r2.get_object_prefix(_settings(), "tmp/x.jpg")
    except botocore.exceptions.ClientError:
        pass
    else:
        raise AssertionError("expected ClientError to bubble up")
