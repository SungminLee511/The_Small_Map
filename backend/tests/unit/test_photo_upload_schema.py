"""Pydantic schema validation for photo presign payloads (Phase 2.2.5)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.upload import PhotoPresignRequest


def test_accepts_jpeg():
    PhotoPresignRequest.model_validate({"content_type": "image/jpeg"})


def test_accepts_png():
    PhotoPresignRequest.model_validate({"content_type": "image/png"})


def test_accepts_webp():
    PhotoPresignRequest.model_validate({"content_type": "image/webp"})


def test_rejects_other_mime():
    with pytest.raises(ValidationError):
        PhotoPresignRequest.model_validate({"content_type": "image/gif"})


def test_rejects_missing_content_type():
    with pytest.raises(ValidationError):
        PhotoPresignRequest.model_validate({})
