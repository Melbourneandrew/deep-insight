from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.schemas.schema import StartInterviewRequest, StartInterviewResponse
from app.services.start_interview_service import (
    StartInterviewService,
    get_start_interview_service,
)


router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.post(
    "/start-interview",
    response_model=StartInterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_interview(
    request: StartInterviewRequest,
    service: StartInterviewService = Depends(get_start_interview_service),
) -> StartInterviewResponse:
    """Start an interview for an employee"""
    try:
        return service.start_interview(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
