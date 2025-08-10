from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from app.services.schemas.schema import AnswerQuestionRequest, AnswerQuestionResponse
from app.services.answer_question_service import get_answer_question_service


router = APIRouter(prefix="/answer-question", tags=["procedures"])


@router.post("/", response_model=AnswerQuestionResponse, status_code=status.HTTP_201_CREATED)
def answer_question(
    request: AnswerQuestionRequest,
    service = Depends(get_answer_question_service)
) -> AnswerQuestionResponse:
    """Record an employee's answer to a question during an interview."""
    try:
        return service.answer_question(request)
    except ValueError as e:
        # Convert service ValueError to appropriate HTTP status
        error_message = str(e)
        if "not found" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_message)
