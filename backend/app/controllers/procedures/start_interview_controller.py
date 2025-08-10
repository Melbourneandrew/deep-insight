from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.services.schemas.schema import StartInterviewRequest, StartInterviewResponse
from app.services.start_interview_service import get_start_interview_service


router = APIRouter(prefix="/start-interview", tags=["procedures"])


@router.post("/", response_model=StartInterviewResponse, status_code=status.HTTP_201_CREATED)
def start_interview(
    request: StartInterviewRequest, session: Session = Depends(get_session)
) -> StartInterviewResponse:
    """Start a new interview for an employee."""
    try:
        service = get_start_interview_service()
        return service.start_interview(request, session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
