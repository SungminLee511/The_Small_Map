"""Photo PIPA pipeline: blur faces / license plates (Phase 2.2.6).

Production should plug in a real detector (RetinaFace / YOLO). For v1 we
ship a ``Detector`` protocol with a no-op default; CI tests the blur
helper itself with a hand-crafted box list.

The blur is intentionally lossy (Gaussian, 25px radius by default) so
that even a partial mask removes biometric information. We also strip
EXIF on output to drop GPS / device hints.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Protocol

from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

DEFAULT_BLUR_RADIUS = 25


@dataclass(frozen=True)
class BlurBox:
    """Pixel-coordinate axis-aligned bounding box."""

    x: int
    y: int
    w: int
    h: int

    def clamp(self, img_w: int, img_h: int) -> "BlurBox":
        x = max(0, min(self.x, img_w))
        y = max(0, min(self.y, img_h))
        w = max(0, min(self.w, img_w - x))
        h = max(0, min(self.h, img_h - y))
        return BlurBox(x, y, w, h)

    @property
    def is_empty(self) -> bool:
        return self.w <= 0 or self.h <= 0


class Detector(Protocol):
    def detect(self, image: Image.Image) -> list[BlurBox]: ...


class NoopDetector:
    """Default v1 detector — finds nothing. Real detector wired in prod."""

    def detect(self, image: Image.Image) -> list[BlurBox]:  # noqa: ARG002
        return []


def apply_blur(
    image_bytes: bytes,
    boxes: list[BlurBox],
    *,
    radius: int = DEFAULT_BLUR_RADIUS,
) -> bytes:
    """Return JPEG bytes with each box gaussian-blurred. EXIF stripped."""
    img = Image.open(io.BytesIO(image_bytes))
    # Apply EXIF orientation, then drop EXIF entirely on output
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    for raw in boxes:
        b = raw.clamp(img.width, img.height)
        if b.is_empty:
            continue
        region = img.crop((b.x, b.y, b.x + b.w, b.y + b.h))
        region = region.filter(ImageFilter.GaussianBlur(radius=radius))
        img.paste(region, (b.x, b.y))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()


def process_photo_bytes(
    image_bytes: bytes, *, detector: Detector | None = None
) -> tuple[bytes, int]:
    """Detect + blur. Returns ``(processed_bytes, num_boxes_blurred)``."""
    det = detector or NoopDetector()
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")
    boxes = det.detect(img)
    out = apply_blur(image_bytes, boxes)
    return out, len(boxes)
