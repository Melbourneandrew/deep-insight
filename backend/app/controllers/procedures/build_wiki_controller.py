from __future__ import annotations

from app.services.build_wiki_service import get_build_wiki_service
from app.services.schemas.schema import BuildWikiRequest, BuildWikiResponse
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/build-wiki", tags=["procedures"])


@router.post("/", response_model=BuildWikiResponse, status_code=status.HTTP_201_CREATED)
async def build_wiki(
    request: BuildWikiRequest,
    service = Depends(get_build_wiki_service)
) -> BuildWikiResponse:
    """Build wiki documentation from interview data for a business."""
    try:
        return await service.build_wiki(request)
    except ValueError as e:
        # Convert service ValueError to appropriate HTTP status
        error_message = str(e)
        if "not found" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "no interview data" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_message)
