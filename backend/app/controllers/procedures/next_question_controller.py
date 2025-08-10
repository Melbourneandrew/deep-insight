from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.schemas.schema import NextQuestionRequest, NextQuestionResponse
from app.services.next_question_service import (
    NextQuestionService,
    get_next_question_service,
)


router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.post("/next-question", response_model=NextQuestionResponse)
def get_next_question(
    request: NextQuestionRequest,
    service: NextQuestionService = Depends(get_next_question_service),
) -> NextQuestionResponse:
    """Get the next question for an interview"""
    try:
        return service.get_next_question(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
