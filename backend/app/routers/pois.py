from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.poi import POIType
from app.schemas.poi import BBox, POIDetail, POIListResponse
from app.services.poi_service import get_poi_by_id, list_pois_in_bbox

router = APIRouter(tags=["pois"])


@router.get("/pois", response_model=POIListResponse)
async def get_pois(
    bbox: str = Query(..., description="west,south,east,north"),
    type: list[POIType] | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    # Parse bbox
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(status_code=422, detail="bbox must be 4 comma-separated floats")

    try:
        west, south, east, north = [float(p.strip()) for p in parts]
    except ValueError:
        raise HTTPException(status_code=422, detail="bbox values must be floats")

    if west >= east:
        raise HTTPException(status_code=422, detail="west must be less than east")
    if south >= north:
        raise HTTPException(status_code=422, detail="south must be less than north")
    if (east - west) > 0.5 or (north - south) > 0.5:
        raise HTTPException(status_code=422, detail="bbox span must be < 0.5 degrees")

    bbox_obj = BBox(west=west, south=south, east=east, north=north)
    items, truncated = await list_pois_in_bbox(session, bbox_obj, types=type)
    return POIListResponse(items=items, truncated=truncated)


@router.get("/pois/{poi_id}", response_model=POIDetail)
async def get_poi(
    poi_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    detail = await get_poi_by_id(session, poi_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="POI not found")
    return detail
