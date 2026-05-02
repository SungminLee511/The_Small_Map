"""Unit tests for the photo PIPA pipeline (Phase 2.2.6)."""

from __future__ import annotations

import io

from PIL import Image

from app.core.photo_blur import (
    BlurBox,
    NoopDetector,
    apply_blur,
    process_photo_bytes,
)


def _make_jpeg(width: int = 100, height: int = 100, color=(200, 50, 50)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_blurbox_clamp_inside_image():
    b = BlurBox(10, 10, 20, 20).clamp(100, 100)
    assert (b.x, b.y, b.w, b.h) == (10, 10, 20, 20)
    assert b.is_empty is False


def test_blurbox_clamp_overflows():
    b = BlurBox(90, 90, 50, 50).clamp(100, 100)
    assert b.w == 10 and b.h == 10
    b2 = BlurBox(120, 120, 50, 50).clamp(100, 100)
    assert b2.is_empty


def test_apply_blur_with_no_boxes_returns_jpeg():
    src = _make_jpeg()
    out = apply_blur(src, [])
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG"
    assert img.size == (100, 100)


def test_apply_blur_inside_box_changes_pixels():
    # Two-tone image: red top half, blue bottom half. Blur the seam.
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    img.paste((0, 0, 255), (0, 50, 100, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    src = buf.getvalue()

    out = apply_blur(src, [BlurBox(0, 40, 100, 20)], radius=20)
    out_img = Image.open(io.BytesIO(out)).convert("RGB")
    # In the blurred band the pixel should be a *mix* — not pure red or pure blue
    px = out_img.getpixel((50, 50))
    assert px != (255, 0, 0)
    assert px != (0, 0, 255)


def test_apply_blur_strips_exif():
    src = _make_jpeg()
    # Re-encode with a fake EXIF
    img = Image.open(io.BytesIO(src))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=b"Exif\x00\x00fakeexif")
    out = apply_blur(buf.getvalue(), [])
    out_img = Image.open(io.BytesIO(out))
    # Pillow exposes EXIF via _getexif() / .info; expect no exif bytes
    assert "exif" not in out_img.info


def test_process_photo_bytes_with_noop_detector_returns_same_dimensions():
    src = _make_jpeg(width=128, height=64)
    out, n_boxes = process_photo_bytes(src, detector=NoopDetector())
    assert n_boxes == 0
    img = Image.open(io.BytesIO(out))
    assert img.size == (128, 64)


def test_process_photo_bytes_runs_custom_detector():
    src = _make_jpeg()

    class StubDetector:
        def detect(self, image):  # noqa: ARG002
            return [BlurBox(10, 10, 30, 30)]

    out, n = process_photo_bytes(src, detector=StubDetector())
    assert n == 1
    assert Image.open(io.BytesIO(out)).format == "JPEG"
