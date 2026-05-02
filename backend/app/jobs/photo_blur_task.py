"""Background task that blurs the photo for a POI (Phase 2.2.6).

Triggered from the POI submission endpoint via FastAPI's BackgroundTasks.
Pulls the canonical R2 object, runs ``process_photo_bytes`` (no-op
detector by default), and uploads the result back to the same key.
On success, sets ``poi.photo_processed_at`` so the frontend can switch
from the placeholder to the real photo.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core import r2
from app.core.photo_blur import process_photo_bytes
from app.db import async_session_factory
from app.models.poi import POI

logger = logging.getLogger(__name__)


async def blur_photo_for_poi(poi_id: uuid.UUID, settings) -> None:
    """Run the PIPA pipeline for a single POI's photo. Idempotent."""
    if not (settings.r2_account_id and settings.r2_access_key_id):
        logger.info("R2 not configured; skipping blur for poi=%s", poi_id)
        return

    # Look up the canonical key from the POI row
    async with async_session_factory() as session:
        poi = (
            await session.execute(select(POI).where(POI.id == poi_id))
        ).scalar_one_or_none()
        if poi is None or not poi.photo_url:
            logger.warning("blur: poi=%s has no photo_url", poi_id)
            return
        if poi.photo_processed_at is not None:
            return  # already processed

        # Recover key from public URL or the r2:// pseudo-url
        key = _extract_key(poi.photo_url, settings)
        if not key:
            logger.error("blur: cannot derive R2 key from %s", poi.photo_url)
            return

        try:
            client = _client(settings)
            obj = client.get_object(Bucket=settings.r2_bucket, Key=key)
            raw = obj["Body"].read()
        except Exception:  # noqa: BLE001
            logger.exception("blur: GET failed for %s", key)
            return

        try:
            processed, n_boxes = process_photo_bytes(raw)
        except Exception:  # noqa: BLE001
            logger.exception("blur: PIL processing failed for %s", key)
            return

        try:
            client.put_object(
                Bucket=settings.r2_bucket,
                Key=key,
                Body=processed,
                ContentType="image/jpeg",
            )
        except Exception:  # noqa: BLE001
            logger.exception("blur: PUT failed for %s", key)
            return

        poi.photo_processed_at = datetime.now(timezone.utc)
        await session.commit()
        logger.info(
            "blur: processed poi=%s (boxes=%d, key=%s)", poi_id, n_boxes, key
        )


def _client(settings):
    # Re-use the same factory r2.py uses so creds match.
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _extract_key(photo_url: str, settings) -> str | None:
    base = settings.r2_public_base_url.rstrip("/")
    if base and photo_url.startswith(base):
        return photo_url[len(base) :].lstrip("/")
    prefix = f"r2://{settings.r2_bucket}/"
    if photo_url.startswith(prefix):
        return photo_url[len(prefix) :]
    return None


__all__ = ["blur_photo_for_poi", "r2"]
